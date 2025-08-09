// workerApi.mjs
function getPromiseAndResolve(): {
  promise: Promise<{ result: any; error: any }>;
  resolve: any;
} {
  let resolve;
  let promise = new Promise((res) => {
    resolve = res;
  }) as any;
  return { promise, resolve };
}

// Each message needs a unique id to identify the response. In a real example,
// we might use a real uuid package
let lastId = 1;
function getId() {
  return lastId++;
}

// Add an id to msg, send it to worker, then wait for a response with the same id.
// When we get such a response, use it to resolve the promise.
function requestResponse(worker: Worker, msg: { context: any; python: any }) {
  const { promise, resolve } = getPromiseAndResolve();
  const idWorker = getId();
  worker.addEventListener("message", function listener(event) {
    if (event.data?.id !== idWorker) {
      return;
    }
    worker.removeEventListener("message", listener);
    const { id, ...rest } = event.data;
    resolve(rest);
  });
  worker.postMessage({ id: idWorker, ...msg });
  return promise;
}

const pyodideWorker = new Worker("./webworker.mjs", { type: "module" });

export function asyncRun(
  script: string,
  context: any = {}
): Promise<{ result: any; error: any }> {
  return requestResponse(pyodideWorker, {
    context,
    python: script,
  });
}
