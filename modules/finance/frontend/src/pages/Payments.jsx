import { METHOD_LABEL, mnt } from "../format";

export default function Payments({ data }) {
  const byId = Object.fromEntries(data.invoices.map((i) => [i.id, i]));
  const rows = [...data.payments].sort((a, b) => b.date.localeCompare(a.date));
  const total = rows.reduce((s, p) => s + p.amount, 0);
  return (
    <>
      <header className="page-head">
        <h1>Төлбөр</h1>
        <p className="muted">{rows.length} гүйлгээ · нийт {mnt(total)}. Төлбөрийг «Нэхэмжлэх» хуудаснаас бүртгэнэ.</p>
      </header>
      <section className="panel flush">
        <div className="scroll">
          <table>
            <thead><tr><th>Огноо</th><th>Нэхэмжлэх</th><th>Харилцагч</th><th>Хэлбэр</th><th className="num">Дүн</th></tr></thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.id}>
                  <td>{p.date}</td>
                  <td>{byId[p.invoiceId]?.number}</td>
                  <td>{byId[p.invoiceId]?.customer}</td>
                  <td>{METHOD_LABEL[p.method]}</td>
                  <td className="num">{mnt(p.amount)}</td>
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan="5" className="empty">Төлбөр бүртгэгдээгүй байна. Нэхэмжлэх хуудаснаас эхний төлбөрөө бүртгэнэ үү.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
