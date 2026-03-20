import { DatabaseSync } from "node:sqlite";
const db = new DatabaseSync(":memory:");
console.log(typeof db.transaction);
