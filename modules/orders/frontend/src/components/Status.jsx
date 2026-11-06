import { STATUS_LABEL } from "../format";

export default function Status({ s }) {
  return <span className={`pill st-${s}`}>{STATUS_LABEL[s] || s}</span>;
}
