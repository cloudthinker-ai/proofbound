import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { setImmediate } from "node:timers/promises";

const [source, caseName, count] = process.argv.slice(2);
const iterations = Number(count);
if (!source || !caseName || !Number.isSafeInteger(iterations) || iterations < 1) {
  throw new Error("Expected upstream source, benchmark case, and positive iteration count");
}
const { name, defineProof } = await import(pathToFileURL(resolve(source)).href);
const issuer = defineProof("Benchmark");

function protectedCall(user, project, proof, value) {
  return value ^ project.value;
}

function protectedFlow(user, project, proof) {
  return user.value + project.value;
}

function batch(operation) {
  let checksum = 0;
  for (let index = 0; index < iterations; index++) {
    checksum = (checksum + operation(index & 1023)) >>> 0;
  }
  return checksum;
}

async function measure(operation) {
  for (let warmup = 0; warmup < 2; warmup++) {
    batch(operation);
    await setImmediate();
  }
  const cpu = process.cpuUsage();
  const start = process.hrtime.bigint();
  const checksum = batch(operation);
  const wall = process.hrtime.bigint() - start;
  const used = process.cpuUsage(cpu);
  return { wall_ns: Number(wall), cpu_ns: (used.user + used.system) * 1000, checksum };
}

async function run() {
  switch (caseName) {
    case "baseline":
      return measure((value) => value);
    case "name1":
      return measure((value) => name(value, (named) => named.value));
    case "name2":
      return measure((value) => name(value, 17, (first, second) => first.value + second.value));
    case "name3":
      return measure((value) => name(value, 17, 42, (first, second, third) => first.value + second.value + third.value));
    case "prove0":
    case "prove1":
    case "prove2":
    case "prove3":
    case "typed_prove2":
      return name(1, 7, 3, async (user, project, third) => {
        const count = caseName === "typed_prove2" ? 2 : Number(caseName.slice(5));
        const issue = [
          () => issuer.prove(),
          () => issuer.prove(user),
          () => issuer.prove(user, project),
          () => issuer.prove(user, project, third),
        ][count];
        let last;
        const result = await measure((value) => {
          last = issue();
          return value ^ last.kind.length;
        });
        if (last !== issue() || !Object.isFrozen(last)) {
          throw new Error("Upstream proof-reuse invariant changed");
        }
        return result;
      });
    case "runtime_require2":
    case "typed_require2":
      return name(1, 7, async (user, project) => {
        const proof = issuer.prove(user, project);
        return measure((value) => protectedCall(user, project, proof, value));
      });
    case "typed_flow2":
    case "runtime_scope_flow2":
      return measure((value) => name(value, 17, (user, project) => {
        const proof = issuer.prove(user, project);
        return protectedFlow(user, project, proof);
      }));
    default:
      throw new Error("Unknown core benchmark case");
  }
}

const sample = await run();
console.log(JSON.stringify({ case: caseName, iterations, ...sample }));
