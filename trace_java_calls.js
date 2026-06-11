import Java from "frida-java-bridge";

const PACKAGE_PREFIX = "com.example.android.architecture.blueprints";
const EXCLUDE_GENERATED = true;

const hookedMethods = new Set<string>();
const visitedClasses = new Set<string>();
const threadStacks: Record<string, string[]> = {};

let scanRound = 0;
let hookedClassCount = 0;

function safeSend(payload: Record<string, unknown>): void {
  try {
    send(payload);
  } catch (_) {
    // Ignore message-delivery failures.
  }
}

function shouldTraceClass(className: string): boolean {
  if (!className.startsWith(PACKAGE_PREFIX)) {
    return false;
  }

  if (!EXCLUDE_GENERATED) {
    return true;
  }

  return !(
    className.includes("$") ||
    className.includes("_Impl") ||
    className.includes("_Factory") ||
    className.includes("_HiltModules") ||
    className.includes("ComposableSingletons") ||
    className.includes("ExternalSynthetic")
  );
}

function getTypeName(typeObject: any): string {
  if (typeObject === null || typeObject === undefined) {
    return "void";
  }

  try {
    if (typeObject.className) {
      return String(typeObject.className);
    }
  } catch (_) {
    // Ignore.
  }

  try {
    return String(typeObject);
  } catch (_) {
    return "unknown";
  }
}

function getThreadStack(threadId: number): string[] {
  const key = String(threadId);

  if (!threadStacks[key]) {
    threadStacks[key] = [];
  }

  return threadStacks[key];
}

function buildMethodId(
  className: string,
  methodName: string,
  overload: any
): string {
  const argumentTypes = overload.argumentTypes
    .map(getTypeName)
    .join(", ");

  const returnType = getTypeName(overload.returnType);

  return `${className}->${methodName}(${argumentTypes}): ${returnType}`;
}

function enterMethod(
  methodId: string,
  className: string,
  methodName: string
): void {
  const threadId = Process.getCurrentThreadId();
  const stack = getThreadStack(threadId);
  const caller = stack.length > 0 ? stack[stack.length - 1] : null;

  safeSend({
    type: "call",
    threadId,
    caller,
    callee: methodId,
    className,
    methodName,
    timestamp: Date.now()
  });

  stack.push(methodId);
}

function leaveMethod(): void {
  const threadId = Process.getCurrentThreadId();
  const stack = getThreadStack(threadId);

  if (stack.length > 0) {
    stack.pop();
  }
}

function hookMethodOverloads(
  className: string,
  methodName: string,
  methodWrapper: any
): number {
  if (!methodWrapper || !methodWrapper.overloads) {
    return 0;
  }

  let newlyHooked = 0;

  methodWrapper.overloads.forEach((overload: any) => {
    const methodId = buildMethodId(className, methodName, overload);

    if (hookedMethods.has(methodId)) {
      return;
    }

    try {
      overload.implementation = function (...args: any[]) {
        enterMethod(methodId, className, methodName);

        try {
          return overload.call(this, ...args);
        } finally {
          leaveMethod();
        }
      };

      hookedMethods.add(methodId);
      newlyHooked += 1;
    } catch (_) {
      // Some methods cannot be replaced. Skip them.
    }
  });

  return newlyHooked;
}

function hookClass(className: string): number {
  if (!shouldTraceClass(className) || visitedClasses.has(className)) {
    return 0;
  }

  let clazz: any;

  try {
    clazz = Java.use(className);
  } catch (_) {
    return 0;
  }

  visitedClasses.add(className);

  const methodNames: Record<string, boolean> = {};
  let newlyHooked = 0;

  try {
    const declaredMethods = clazz.class.getDeclaredMethods();

    for (let index = 0; index < declaredMethods.length; index += 1) {
      methodNames[String(declaredMethods[index].getName())] = true;
    }
  } catch (_) {
    // Ignore.
  }

  Object.keys(methodNames).forEach((methodName) => {
    try {
      newlyHooked += hookMethodOverloads(
        className,
        methodName,
        clazz[methodName]
      );
    } catch (_) {
      // Ignore individual methods.
    }
  });

  try {
    if (clazz.$init) {
      newlyHooked += hookMethodOverloads(className, "$init", clazz.$init);
    }
  } catch (_) {
    // Ignore.
  }

  if (newlyHooked > 0) {
    hookedClassCount += 1;
  }

  return newlyHooked;
}

function scanLoadedClasses(): void {
  Java.perform(() => {
    let loadedClasses: string[] = [];

    try {
      loadedClasses = Java.enumerateLoadedClassesSync();
    } catch (error) {
      safeSend({
        type: "agent_error",
        message: `enumerateLoadedClassesSync failed: ${String(error)}`
      });
      return;
    }

    let newlyHookedMethods = 0;

    loadedClasses.forEach((className) => {
      try {
        newlyHookedMethods += hookClass(className);
      } catch (_) {
        // Ignore individual classes.
      }
    });

    scanRound += 1;

    safeSend({
      type: "scan",
      scanRound,
      loadedClassCount: loadedClasses.length,
      hookedClassCount,
      hookedMethodCount: hookedMethods.size,
      newlyHookedMethodCount: newlyHookedMethods
    });
  });
}

function start(): void {
  if (!Java.available) {
    safeSend({
      type: "agent_error",
      message: "Java VM is not available in the target process."
    });
    return;
  }

  safeSend({
    type: "ready",
    message: "Java bridge loaded. Starting method scan."
  });

  scanLoadedClasses();
  setInterval(scanLoadedClasses, 1500);
}

setImmediate(start);
