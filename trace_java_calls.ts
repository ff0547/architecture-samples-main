import Java from "frida-java-bridge";

const PACKAGE_PREFIX =
  "com.example.android.architecture.blueprints";

const EXCLUDE_GENERATED = false;

const ROOT_NODE =
  "ROOT::FrameworkOrAsyncEntry";

const hookedMethods =
  new Set<string>();

const visitedClasses =
  new Set<string>();

const threadStacks:
  Record<string, string[]> = {};

let scanRound = 0;

let hookedClassCount = 0;


/**
 * 安全发送消息。
 */
function safeSend(
  payload: Record<string, unknown>
): void {
  try {
    send(payload);
  } catch (_) {
    // Ignore.
  }
}


/**
 * 判断类是否属于项目。
 */
function isProjectClass(
  className: string
): boolean {
  return className.startsWith(
    PACKAGE_PREFIX
  );
}


/**
 * 判断是否 Hook 当前类。
 */
function shouldTraceClass(
  className: string
): boolean {
  if (!isProjectClass(className)) {
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


/**
 * 获取方法类型名称。
 */
function getTypeName(
  typeObject: any
): string {
  if (
    typeObject === null ||
    typeObject === undefined
  ) {
    return "void";
  }

  try {
    if (typeObject.className) {
      return String(
        typeObject.className
      );
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


/**
 * 为不同线程维护独立调用栈。
 */
function getThreadStack(
  threadId: number
): string[] {
  const key =
    String(threadId);

  if (!threadStacks[key]) {
    threadStacks[key] = [];
  }

  return threadStacks[key];
}


/**
 * 生成完整方法签名。
 */
function buildMethodId(
  className: string,
  methodName: string,
  overload: any
): string {
  const argumentTypes =
    overload.argumentTypes
      .map(getTypeName)
      .join(", ");

  const returnType =
    getTypeName(
      overload.returnType
    );

  return (
    `${className}->${methodName}` +
    `(${argumentTypes}): ${returnType}`
  );
}


/**
 * 根据 Java 调用栈推断最近的项目调用者。
 *
 * 当前同步调用栈为空时使用。
 */
function inferCallerFromBacktrace(
  calleeClassName: string,
  calleeMethodName: string
): string | null {
  try {
    const trace =
      Java.backtrace({
        limit: 32
      });

    for (
      let index = 0;
      index < trace.frames.length;
      index += 1
    ) {
      const frame =
        trace.frames[index];

      const frameClassName =
        String(frame.className);

      const frameMethodName =
        String(frame.methodName);

      if (
        frameClassName ===
          calleeClassName &&
        frameMethodName ===
          calleeMethodName
      ) {
        continue;
      }

      if (
        isProjectClass(
          frameClassName
        )
      ) {
        return (
          `${frameClassName}` +
          `->${frameMethodName}` +
          `(backtrace)`
        );
      }
    }
  } catch (_) {
    // Ignore.
  }

  return null;
}


/**
 * 进入方法。
 */
function enterMethod(
  methodId: string,
  className: string,
  methodName: string
): void {
  const threadId =
    Process.getCurrentThreadId();

  const stack =
    getThreadStack(threadId);

  let caller:
    string | null = null;

  let edgeType =
    "synchronous";

  if (stack.length > 0) {
    caller =
      stack[
        stack.length - 1
      ];
  } else {
    caller =
      inferCallerFromBacktrace(
        className,
        methodName
      );

    edgeType =
      "backtrace";

    if (!caller) {
      caller =
        ROOT_NODE;

      edgeType =
        "root";
    }
  }

  safeSend({
    type: "call",
    threadId,
    caller,
    callee: methodId,
    className,
    methodName,
    edgeType,
    timestamp: Date.now()
  });

  stack.push(methodId);
}


/**
 * 离开方法。
 */
function leaveMethod(): void {
  const threadId =
    Process.getCurrentThreadId();

  const stack =
    getThreadStack(threadId);

  if (stack.length > 0) {
    stack.pop();
  }
}


/**
 * Hook 方法的全部重载。
 */
function hookMethodOverloads(
  className: string,
  methodName: string,
  methodWrapper: any
): number {
  if (
    !methodWrapper ||
    !methodWrapper.overloads
  ) {
    return 0;
  }

  let newlyHooked = 0;

  methodWrapper.overloads.forEach(
    (overload: any) => {
      const methodId =
        buildMethodId(
          className,
          methodName,
          overload
        );

      if (
        hookedMethods.has(
          methodId
        )
      ) {
        return;
      }

      try {
        overload.implementation =
          function (
            ...args: any[]
          ) {
            enterMethod(
              methodId,
              className,
              methodName
            );

            try {
              return overload.call(
                this,
                ...args
              );
            } finally {
              leaveMethod();
            }
          };

        hookedMethods.add(
          methodId
        );

        newlyHooked += 1;

      } catch (_) {
        // Ignore methods that cannot be replaced.
      }
    }
  );

  return newlyHooked;
}


/**
 * Hook 单个类。
 */
function hookClass(
  className: string
): number {
  if (
    !shouldTraceClass(
      className
    ) ||
    visitedClasses.has(
      className
    )
  ) {
    return 0;
  }

  let clazz: any;

  try {
    clazz =
      Java.use(className);
  } catch (_) {
    return 0;
  }

  visitedClasses.add(
    className
  );

  const methodNames:
    Record<string, boolean> = {};

  let newlyHooked = 0;

  try {
    const declaredMethods =
      clazz.class
        .getDeclaredMethods();

    for (
      let index = 0;
      index <
        declaredMethods.length;
      index += 1
    ) {
      const methodName =
        String(
          declaredMethods[
            index
          ].getName()
        );

      methodNames[
        methodName
      ] = true;
    }
  } catch (_) {
    // Ignore.
  }

  Object.keys(
    methodNames
  ).forEach(
    (methodName) => {
      try {
        newlyHooked +=
          hookMethodOverloads(
            className,
            methodName,
            clazz[
              methodName
            ]
          );
      } catch (_) {
        // Ignore.
      }
    }
  );

  try {
    if (clazz.$init) {
      newlyHooked +=
        hookMethodOverloads(
          className,
          "$init",
          clazz.$init
        );
    }
  } catch (_) {
    // Ignore.
  }

  if (newlyHooked > 0) {
    hookedClassCount += 1;
  }

  return newlyHooked;
}


/**
 * 扫描当前已经加载的类。
 */
function scanLoadedClasses(): void {
  Java.perform(() => {
    let loadedClasses:
      string[] = [];

    try {
      loadedClasses =
        Java
          .enumerateLoadedClassesSync();
    } catch (error) {
      safeSend({
        type:
          "agent_error",

        message:
          "enumerateLoadedClassesSync failed: " +
          String(error)
      });

      return;
    }

    let newlyHookedMethods =
      0;

    loadedClasses.forEach(
      (className) => {
        try {
          newlyHookedMethods +=
            hookClass(
              className
            );
        } catch (_) {
          // Ignore.
        }
      }
    );

    scanRound += 1;

    safeSend({
      type: "scan",
      scanRound,
      loadedClassCount:
        loadedClasses.length,
      hookedClassCount,
      hookedMethodCount:
        hookedMethods.size,
      newlyHookedMethodCount:
        newlyHookedMethods
    });
  });
}


/**
 * Agent 入口。
 */
function start(): void {
  if (!Java.available) {
    safeSend({
      type: "agent_error",
      message:
        "Java VM is not available."
    });

    return;
  }

  safeSend({
    type: "ready",
    message:
      "Java bridge loaded. Starting method scan."
  });

  scanLoadedClasses();

  setInterval(
    scanLoadedClasses,
    1500
  );
}


setImmediate(start);