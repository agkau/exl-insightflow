/** Encode data faithfully for spreadsheet review, escaping formulas and quoting fields. */
export function toCSV(rows){
  if (!rows.length) return '';
  const keys=Object.keys(rows[0]);
  const quote = value => {
    const str=String(value ?? '');
    // Neutralize formula-like values when a CSV is opened in spreadsheet software.
    const clean=/^[\t\r\n]*[=+@]/.test(str) ? "'"+str : str;
    return '"'+clean.replaceAll('"','""')+'"';
  };
  return [keys.map(quote).join(','),...rows.map(row=>keys.map(k=>quote(row[k])).join(','))].join('\r\n');
}
