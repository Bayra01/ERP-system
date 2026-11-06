// Frontend ni hiigdeegui modulid haragdana.
export default function Placeholder({ module, page }) {
  return (
    <>
      <header className="page-head">
        <h1>{module.label}</h1>
        <p className="muted">{page?.label}</p>
      </header>
      <section className="panel">
        <h2>Хөгжүүлэлт хийгдэж байна</h2>
        <p className="muted">
          Энэ модулийн backend бэлэн (<code>{module.prefix}</code>) боловч интерфэйс хараахан хийгдээгүй байна.
          Код нь <code>modules/{module.id}/frontend/</code> дотор байрлана.
        </p>
      </section>
    </>
  );
}
