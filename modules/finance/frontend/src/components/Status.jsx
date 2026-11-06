import { STATUS_LABEL } from "../format";
export default function Status({ s }) {
  return <span className={"pill " + s}>{STATUS_LABEL[s]}</span>;
}
