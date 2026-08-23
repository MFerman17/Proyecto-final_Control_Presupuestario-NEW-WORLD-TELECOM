/* ============================================================
   New World Telecom — Dashboard interactivo
   Reutiliza DATA (bundle JSON embebido en index.html)
   ============================================================ */

const MESES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
const COLORS = {
  navy:'#0E2A47', teal:'#17B8AE', tealLight:'rgba(23,184,174,.18)',
  amber:'#E8A33D', alert:'#E15759', ok:'#3FA796', gray:'#9AA6B2',
  navyLight:'rgba(14,42,71,.55)'
};

/* ---------- Lookups & enrichment ---------- */
const deptById = Object.fromEntries(DATA.departamentos.map(d=>[d.departamento_id, d.nombre]));
const catById  = Object.fromEntries(DATA.categorias.map(c=>[c.categoria_id, c.nombre]));
const perById  = Object.fromEntries(DATA.periodos.map(p=>[p.periodo_id, p]));
const deptList = DATA.departamentos.map(d=>d.nombre).sort();
const catList  = DATA.categorias.map(c=>c.nombre).sort();

function enrich(rows){
  return rows.map(r=>{
    const per = perById[r.periodo_id] || {};
    return Object.assign({}, r, {
      departamento: deptById[r.departamento_id],
      categoria: r.categoria_id!=null ? catById[r.categoria_id] : undefined,
      anio: per.anio, mes: per.mes,
    });
  });
}

const PRESUPUESTO = enrich(DATA.presupuesto);
const EJECUCION   = enrich(DATA.ejecucion_real_limpia);
const INGRESOS    = enrich(DATA.ingresos);
const KPI         = enrich(DATA.kpi_presupuesto_detallado);
const ING_FC      = enrich(DATA.ingresos_forecast_2026);
const PRES_26     = enrich(DATA.presupuesto_2026);
const GASTO_26    = enrich(DATA.gasto_esperado_2026);
const RESUMEN     = DATA.resumen_financiero_mensual.slice().sort((a,b)=>a.mes-b.mes);

/* ---------- Formatters ---------- */
function fmtCompactEUR(n){
  if(n==null || isNaN(n)) return '—';
  const abs = Math.abs(n);
  if(abs>=1e6) return (n/1e6).toFixed(2).replace('.',',')+' mill.€';
  if(abs>=1e3) return (n/1e3).toFixed(0)+' mil €';
  return Math.round(n).toLocaleString('es-ES')+' €';
}
function fmtEUR2(n){
  if(n==null || isNaN(n)) return '—';
  return n.toLocaleString('es-ES',{maximumFractionDigits:0})+' €';
}
function fmtPct(n,d=1){
  if(n==null || isNaN(n)) return '—';
  return (n*100).toFixed(d).replace('.',',')+'%';
}
function sum(arr, f){ return arr.reduce((a,r)=> a + (typeof f==='function'? (f(r)||0) : (r[f]||0)), 0); }
function avg(arr, f){ return arr.length ? sum(arr,f)/arr.length : 0; }

/* ---------- Generic filter helpers ---------- */
function applyFilters(rows, filters){
  const mesNum = filters.mes && filters.mes!=='Todas' ? MESES.indexOf(filters.mes)+1 : null;
  return rows.filter(r=>{
    if(mesNum && r.mes!==mesNum) return false;
    if(filters.departamento && filters.departamento!=='Todas' && r.departamento!==filters.departamento) return false;
    if(filters.categoria && filters.categoria!=='Todas' && r.categoria!==filters.categoria) return false;
    if(filters.concepto && filters.concepto!=='Todas' && r.concepto!==filters.concepto) return false;
    return true;
  });
}
function selectHTML(id, label, options){
  return `<div class="filter"><label>${label}</label>
    <select id="${id}"><option>Todas</option>${options.map(o=>`<option>${o}</option>`).join('')}</select></div>`;
}

/* ---------- Chart registry (para destruir antes de re-crear) ---------- */
const charts = {};
function makeChart(canvasId, config){
  if(charts[canvasId]) charts[canvasId].destroy();
  const ctx = document.getElementById(canvasId);
  charts[canvasId] = new Chart(ctx, config);
}

/* ============================================================
   PAGE DEFINITIONS
   ============================================================ */
const PAGES = [
  {id:'resumen', label:'Resumen General'},
  {id:'ingresos', label:'Ingresos'},
  {id:'gastos', label:'Gastos'},
  {id:'presupuesto', label:'Presupuesto'},
  {id:'forecast', label:'Forecast 2026'},
  {id:'detalle', label:'Detalles'},
];

function skeletons(){
  return {
    resumen: `
      <div class="page-title">Resumen General</div>
      <div class="page-sub">Vista consolidada del ejercicio 2025</div>
      <div class="filters">
        ${selectHTML('r-mes','Mes',MESES)}
        ${selectHTML('r-dept','Departamento',deptList)}
        ${selectHTML('r-cat','Categoría',catList)}
      </div>
      <div class="kpirow" id="r-kpis"></div>
      <div class="grid2">
        <div class="card"><h3>Ingresos reales vs. Presupuesto por mes</h3><div class="cardsub">Serie mensual 2025</div>
          <div class="chartwrap"><canvas id="r-chart-trend"></canvas></div></div>
        <div class="card"><h3>Distribución de ingresos</h3><div class="cardsub">Por línea de negocio</div>
          <div class="chartwrap"><canvas id="r-chart-donut"></canvas></div></div>
      </div>
      <div class="card"><h3>Presupuesto vs. Gasto ejecutado por departamento</h3>
        <div class="chartwrap"><canvas id="r-chart-bar"></canvas></div></div>
    `,
    ingresos: `
      <div class="page-title">Ingresos</div>
      <div class="page-sub">Evolución y participación por línea de negocio — 2025</div>
      <div class="filters">
        ${selectHTML('i-mes','Mes',MESES)}
        ${selectHTML('i-concepto','Línea de negocio',[...new Set(INGRESOS.map(r=>r.concepto))])}
      </div>
      <div class="kpirow" id="i-kpis"></div>
      <div class="card"><h3>Evolución mensual por línea de negocio</h3>
        <div class="chartwrap tall"><canvas id="i-chart-line"></canvas></div></div>
      <div class="card" style="margin-top:16px;"><h3>Participación y crecimiento por línea</h3>
        <div class="cardsub">% de participación respetando el filtro de mes (equivalente a ALLSELECTED en DAX)</div>
        <div class="tablewrap"><table class="datatable" id="i-table"></table></div></div>
    `,
    gastos: `
      <div class="page-title">Gastos</div>
      <div class="page-sub">Ejecución real vs. presupuestado — 2025</div>
      <div class="filters">
        ${selectHTML('g-mes','Mes',MESES)}
        ${selectHTML('g-dept','Departamento',deptList)}
        ${selectHTML('g-cat','Categoría',catList)}
      </div>
      <div class="kpirow" id="g-kpis"></div>
      <div class="card"><h3>Desviación por categoría</h3><div class="cardsub">Gasto ejecutado − Presupuesto (verde = ahorro, rojo = sobreejecución)</div>
        <div class="chartwrap"><canvas id="g-chart-dev"></canvas></div></div>
      <div class="card" style="margin-top:16px;"><h3>Detalle por departamento y categoría</h3>
        <div class="tablewrap"><table class="datatable" id="g-table"></table></div></div>
    `,
    presupuesto: `
      <div class="page-title">Presupuesto</div>
      <div class="page-sub">Planificación 2025</div>
      <div class="filters">
        ${selectHTML('p-mes','Mes',MESES)}
        ${selectHTML('p-dept','Departamento',deptList)}
        ${selectHTML('p-cat','Categoría',catList)}
      </div>
      <div class="kpirow" id="p-kpis"></div>
      <div class="grid2">
        <div class="card"><h3>Presupuesto por departamento</h3>
          <div class="chartwrap"><canvas id="p-chart-bar"></canvas></div></div>
        <div class="card"><h3>% Ejecución del presupuesto</h3><div class="cardsub">Meta: 100%</div>
          <div id="p-gauge" style="padding-top:30px;"></div></div>
      </div>
      <div class="card"><h3>Presupuesto por departamento y mes</h3>
        <div class="tablewrap"><table class="datatable" id="p-matrix"></table></div></div>
    `,
    forecast: `
      <div class="page-title">Forecast 2026</div>
      <div class="page-sub">Proyección estadística de ingresos, presupuesto planificado y gasto esperado</div>
      <div class="filters">${selectHTML('f-dept','Departamento',deptList)}</div>
      <div class="kpirow" id="f-kpis"></div>
      <div class="card"><h3>Ingresos forecast 2026 con banda de confianza 95%</h3>
        <div class="chartwrap tall"><canvas id="f-chart-band"></canvas></div></div>
      <div class="card" style="margin-top:16px;"><h3>Gasto esperado 2026 por mes</h3>
        <div class="chartwrap"><canvas id="f-chart-gasto"></canvas></div></div>
    `,
    detalle: `
      <div class="page-title">Detalles</div>
      <div class="page-sub">Tabla granular — presupuesto, ejecución y KPIs por departamento, categoría y mes</div>
      <div class="filters">
        ${selectHTML('d-mes','Mes',MESES)}
        ${selectHTML('d-dept','Departamento',deptList)}
      </div>
      <div class="searchbox"><input id="d-search" type="text" placeholder="Buscar por departamento o categoría..."></div>
      <div class="tablewrap"><table class="datatable" id="d-table"></table></div>
    `,
  };
}

/* ============================================================
   RENDER: Resumen General
   ============================================================ */
function renderResumen(){
  const f = { mes: val('r-mes'), departamento: val('r-dept'), categoria: val('r-cat') };

  const ing = applyFilters(INGRESOS, {mes:f.mes, departamento:f.departamento});
  const gas = applyFilters(EJECUCION, f);
  const pre = applyFilters(PRESUPUESTO, f);

  const totalIng = sum(ing,'monto_ingresos');
  const totalGas = sum(gas,'monto_ejecutado');
  const totalPre = sum(pre,'monto_presupuestado');
  const margen = totalIng ? (totalIng-totalGas)/totalIng : 0;
  const pctEjec = totalPre ? totalGas/totalPre : 0;

  document.getElementById('r-kpis').innerHTML = [
    kpi(fmtCompactEUR(totalIng),'Total Ingresos'),
    kpi(fmtCompactEUR(totalGas),'Total Gastos'),
    kpi(fmtCompactEUR(totalPre),'Total Presupuesto'),
    kpi(fmtPct(margen),'Margen Operativo %'),
    kpi(fmtPct(pctEjec),'% Ejecución del ppto'),
  ].join('');

  const ingByMes = MESES.map((_,i)=> sum(applyFilters(INGRESOS,{departamento:f.departamento}).filter(r=>r.mes===i+1),'monto_ingresos'));
  const preByMes = MESES.map((_,i)=> sum(applyFilters(PRESUPUESTO,{departamento:f.departamento,categoria:f.categoria}).filter(r=>r.mes===i+1),'monto_presupuestado'));
  makeChart('r-chart-trend', {
    type:'line',
    data:{ labels:MESES, datasets:[
      {label:'Ingresos reales', data:ingByMes, borderColor:COLORS.teal, backgroundColor:COLORS.tealLight, tension:.35, fill:true, pointRadius:2},
      {label:'Presupuesto', data:preByMes, borderColor:COLORS.navy, backgroundColor:'transparent', tension:.35, borderDash:[5,3], pointRadius:2},
    ]},
    options:baseLineOpts(),
  });

  const conceptos = [...new Set(INGRESOS.map(r=>r.concepto))];
  const donutData = conceptos.map(c=> sum(applyFilters(INGRESOS,{mes:f.mes,departamento:f.departamento}).filter(r=>r.concepto===c),'monto_ingresos'));
  makeChart('r-chart-donut', {
    type:'doughnut',
    data:{ labels:conceptos, datasets:[{data:donutData, backgroundColor:[COLORS.teal,COLORS.navy,COLORS.amber], borderWidth:2, borderColor:'#fff'}]},
    options:{ responsive:true, maintainAspectRatio:false, plugins:{legend:{position:'bottom',labels:{boxWidth:12,font:{size:11}}}} },
  });

  const preByDept = deptList.map(d=> sum(applyFilters(PRESUPUESTO,{mes:f.mes,categoria:f.categoria}).filter(r=>r.departamento===d),'monto_presupuestado'));
  const gasByDept = deptList.map(d=> sum(applyFilters(EJECUCION,{mes:f.mes,categoria:f.categoria}).filter(r=>r.departamento===d),'monto_ejecutado'));
  makeChart('r-chart-bar', {
    type:'bar',
    data:{ labels:deptList, datasets:[
      {label:'Presupuesto', data:preByDept, backgroundColor:COLORS.navy, borderRadius:4},
      {label:'Gasto ejecutado', data:gasByDept, backgroundColor:COLORS.teal, borderRadius:4},
    ]},
    options:baseBarOpts(),
  });
}

/* ============================================================
   RENDER: Ingresos
   ============================================================ */
function renderIngresos(){
  const f = { mes: val('i-mes'), concepto: val('i-concepto') };
  const conceptos = [...new Set(INGRESOS.map(r=>r.concepto))];

  const filtered = applyFilters(INGRESOS, {mes:f.mes, concepto:f.concepto});
  const total = sum(filtered,'monto_ingresos');
  const mesesActivos = f.mes==='Todas' ? 12 : 1;
  const promedio = total/mesesActivos;

  const baseMes = applyFilters(INGRESOS,{concepto:f.concepto});
  const ene = sum(baseMes.filter(r=>r.mes===1),'monto_ingresos');
  const dic = sum(baseMes.filter(r=>r.mes===12),'monto_ingresos');
  const crecimiento = ene ? (dic-ene)/ene : 0;

  document.getElementById('i-kpis').innerHTML = [
    kpi(fmtCompactEUR(total),'Total Ingresos'),
    kpi(fmtCompactEUR(promedio),'Ingreso Promedio Mensual'),
    kpi(fmtPct(crecimiento),'% Crecimiento Ene→Dic'),
  ].join('');

  makeChart('i-chart-line', {
    type:'line',
    data:{ labels:MESES, datasets: conceptos.map((c,idx)=>({
      label:c,
      data: MESES.map((_,i)=> sum(INGRESOS.filter(r=>r.mes===i+1 && r.concepto===c),'monto_ingresos')),
      borderColor:[COLORS.teal,COLORS.navy,COLORS.amber][idx%3],
      backgroundColor:'transparent', tension:.35, pointRadius:2,
      hidden: f.concepto!=='Todas' && f.concepto!==c,
    })) },
    options:baseLineOpts(),
  });

  const mesFiltered = applyFilters(INGRESOS,{mes:f.mes});
  const totalParaParticipacion = sum(mesFiltered,'monto_ingresos');
  const rows = conceptos.map(c=>{
    const t = sum(mesFiltered.filter(r=>r.concepto===c),'monto_ingresos');
    const en = sum(INGRESOS.filter(r=>r.concepto===c && r.mes===1),'monto_ingresos');
    const di = sum(INGRESOS.filter(r=>r.concepto===c && r.mes===12),'monto_ingresos');
    const crec = en ? (di-en)/en : 0;
    const part = totalParaParticipacion ? t/totalParaParticipacion : 0;
    return `<tr><td>${c}</td><td>${fmtEUR2(t)}</td><td>${fmtPct(part)}</td><td>${fmtPct(crec)}</td></tr>`;
  }).join('');
  document.getElementById('i-table').innerHTML = `
    <thead><tr><th>Concepto</th><th>Total Ingresos</th><th>% Participación</th><th>Crecimiento Ene→Dic</th></tr></thead>
    <tbody>${rows}</tbody>`;
}

/* ============================================================
   RENDER: Gastos
   ============================================================ */
function renderGastos(){
  const f = { mes: val('g-mes'), departamento: val('g-dept'), categoria: val('g-cat') };
  const pre = applyFilters(PRESUPUESTO, f);
  const gas = applyFilters(EJECUCION, f);
  const totalPre = sum(pre,'monto_presupuestado');
  const totalGas = sum(gas,'monto_ejecutado');
  const pctEjec = totalPre ? totalGas/totalPre : 0;
  const desviacion = totalGas-totalPre;

  document.getElementById('g-kpis').innerHTML = [
    kpi(fmtCompactEUR(totalGas),'Total Gastos'),
    kpi(fmtCompactEUR(totalPre),'Total Presupuesto'),
    kpi(fmtPct(pctEjec),'% Ejecución'),
    kpi(fmtCompactEUR(desviacion),'Desviación Total', desviacion>0?'down':'up'),
  ].join('');

  const devByCat = catList.map(c=>{
    const p = sum(applyFilters(PRESUPUESTO,{mes:f.mes,departamento:f.departamento}).filter(r=>r.categoria===c),'monto_presupuestado');
    const g = sum(applyFilters(EJECUCION,{mes:f.mes,departamento:f.departamento}).filter(r=>r.categoria===c),'monto_ejecutado');
    return g-p;
  });
  makeChart('g-chart-dev', {
    type:'bar',
    data:{ labels:catList, datasets:[{ data:devByCat,
      backgroundColor: devByCat.map(v=> v>0 ? COLORS.alert : COLORS.ok), borderRadius:4 }]},
    options:{ ...baseBarOpts(), plugins:{legend:{display:false}} },
  });

  const rows=[];
  deptList.forEach(d=>{
    catList.forEach(c=>{
      const p = sum(applyFilters(PRESUPUESTO,{mes:f.mes}).filter(r=>r.departamento===d && r.categoria===c),'monto_presupuestado');
      const g = sum(applyFilters(EJECUCION,{mes:f.mes}).filter(r=>r.departamento===d && r.categoria===c),'monto_ejecutado');
      if(p===0 && g===0) return;
      const pct = p ? (g-p)/p : 0;
      const tag = pct>0.10 ? '<span class="tag bad">Sobreejecución</span>' : (pct< -0.05 ? '<span class="tag good">Ahorro</span>' : '<span class="tag neutral">Normal</span>');
      rows.push(`<tr><td>${d}</td><td>${c}</td><td>${fmtEUR2(p)}</td><td>${fmtEUR2(g)}</td><td>${fmtPct(pct)}</td><td>${tag}</td></tr>`);
    });
  });
  document.getElementById('g-table').innerHTML = `
    <thead><tr><th>Departamento</th><th>Categoría</th><th>Presupuesto</th><th>Gasto</th><th>Desviación %</th><th>Estado</th></tr></thead>
    <tbody>${rows.join('')}</tbody>`;
}

/* ============================================================
   RENDER: Presupuesto
   ============================================================ */
function renderPresupuesto(){
  const f = { mes: val('p-mes'), departamento: val('p-dept'), categoria: val('p-cat') };
  const pre = applyFilters(PRESUPUESTO, f);
  const gas = applyFilters(EJECUCION, f);
  const totalPre = sum(pre,'monto_presupuestado');
  const totalGas = sum(gas,'monto_ejecutado');
  const mesesActivos = f.mes==='Todas' ? 12 : 1;
  const promedio = totalPre/mesesActivos;
  const pctEjec = totalPre ? totalGas/totalPre : 0;

  document.getElementById('p-kpis').innerHTML = [
    kpi(fmtCompactEUR(totalPre),'Total Presupuesto'),
    kpi(fmtCompactEUR(promedio),'Presupuesto Promedio Mensual'),
    kpi(fmtPct(pctEjec),'% Ejecución'),
  ].join('');

  const byDept = deptList.map(d=> sum(applyFilters(PRESUPUESTO,{mes:f.mes,categoria:f.categoria}).filter(r=>r.departamento===d),'monto_presupuestado'));
  const order = deptList.map((d,i)=>[d,byDept[i]]).sort((a,b)=>b[1]-a[1]);
  makeChart('p-chart-bar', {
    type:'bar',
    data:{ labels:order.map(o=>o[0]), datasets:[{data:order.map(o=>o[1]), backgroundColor:COLORS.navy, borderRadius:4}]},
    options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins:{legend:{display:false}, tooltip:{callbacks:{label:c=>fmtEUR2(c.raw)}}},
      scales:{x:{ticks:{callback:v=>fmtCompactEUR(v)}}} },
  });

  const pctClamped = Math.max(0, Math.min(pctEjec, 1.2));
  const barColor = pctEjec>1 ? COLORS.alert : COLORS.ok;
  document.getElementById('p-gauge').innerHTML = `
    <div style="text-align:center;font-size:38px;font-weight:800;color:${barColor};">${fmtPct(pctEjec)}</div>
    <div style="text-align:center;color:var(--muted);font-size:12px;margin-bottom:14px;">del presupuesto ejecutado</div>
    <div style="background:#EEF1F4;border-radius:20px;height:16px;overflow:hidden;">
      <div style="width:${(pctClamped/1.2*100).toFixed(1)}%;background:${barColor};height:100%;border-radius:20px;transition:width .3s;"></div>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--muted);margin-top:4px;">
      <span>0%</span><span>Meta: 100%</span><span>120%</span>
    </div>`;

  let head = '<thead><tr><th>Departamento</th>'+MESES.map(m=>`<th>${m.slice(0,3)}</th>`).join('')+'</tr></thead>';
  let body = deptList.map(d=>{
    const cells = MESES.map((_,i)=> fmtCompactEUR(sum(applyFilters(PRESUPUESTO,{categoria:f.categoria}).filter(r=>r.departamento===d && r.mes===i+1),'monto_presupuestado'))).join('</td><td>');
    return `<tr><td><b>${d}</b></td><td>${cells}</td></tr>`;
  }).join('');
  document.getElementById('p-matrix').innerHTML = head+'<tbody>'+body+'</tbody>';
}

/* ============================================================
   RENDER: Forecast 2026
   ============================================================ */
function renderForecast(){
  const f = { departamento: val('f-dept') };
  const ing = applyFilters(ING_FC, f);
  const pre = applyFilters(PRES_26, f);
  const gas = applyFilters(GASTO_26, f);

  const totalIng = sum(ing,'monto_ingresos_forecast');
  const totalPre = sum(pre,'monto_presupuestado_2026');
  const totalGas = sum(gas,'monto_gasto_esperado');
  const margen = totalIng ? (totalIng-totalGas)/totalIng : 0;

  document.getElementById('f-kpis').innerHTML = [
    kpi(fmtCompactEUR(totalIng),'Ingresos Forecast 2026'),
    kpi(fmtCompactEUR(totalPre),'Presupuesto 2026'),
    kpi(fmtCompactEUR(totalGas),'Gasto Esperado 2026'),
    kpi(fmtPct(margen),'Margen Esperado 2026'),
  ].join('');

  const byMes = i => applyFilters(ING_FC,{departamento:f.departamento}).filter(r=>r.mes===i+1);
  const central = MESES.map((_,i)=> sum(byMes(i),'monto_ingresos_forecast'));
  const min = MESES.map((_,i)=> sum(byMes(i),'monto_min'));
  const max = MESES.map((_,i)=> sum(byMes(i),'monto_max'));
  makeChart('f-chart-band', {
    type:'line',
    data:{ labels:MESES, datasets:[
      {label:'Mínimo (IC 95%)', data:min, borderColor:'transparent', backgroundColor:'transparent', pointRadius:0, order:3},
      {label:'Máximo (IC 95%)', data:max, borderColor:'transparent', backgroundColor:COLORS.tealLight, fill:'-1', pointRadius:0, order:2},
      {label:'Forecast', data:central, borderColor:COLORS.navy, backgroundColor:'transparent', borderWidth:2.5, tension:.35, pointRadius:2, order:1},
    ]},
    options:baseLineOpts(),
  });

  const gasByMes = MESES.map((_,i)=> sum(applyFilters(GASTO_26,{departamento:f.departamento}).filter(r=>r.mes===i+1),'monto_gasto_esperado'));
  makeChart('f-chart-gasto', {
    type:'bar',
    data:{ labels:MESES, datasets:[{data:gasByMes, backgroundColor:COLORS.amber, borderRadius:4}]},
    options:{ ...baseBarOpts(), plugins:{legend:{display:false}} },
  });
}

/* ============================================================
   RENDER: Detalle
   ============================================================ */
function renderDetalle(){
  const f = { mes: val('d-mes'), departamento: val('d-dept') };
  const search = (document.getElementById('d-search').value||'').toLowerCase();
  let rows = applyFilters(KPI, f);
  if(search){
    rows = rows.filter(r=> (r.departamento||'').toLowerCase().includes(search) || (r.categoria||'').toLowerCase().includes(search));
  }
  const body = rows.slice(0,300).map(r=>{
    const tag = r.flag_alerta_sobreejecucion ? '<span class="tag bad">Alerta</span>' : (r.sin_dato_ejecucion ? '<span class="tag neutral">Sin dato</span>' : '<span class="tag good">OK</span>');
    return `<tr><td>${r.departamento}</td><td>${r.categoria}</td><td>${MESES[r.mes-1]}</td><td>${fmtEUR2(r.monto_presupuestado)}</td><td>${r.monto_ejecutado!=null?fmtEUR2(r.monto_ejecutado):'—'}</td><td>${fmtPct(r.pct_ejecucion)}</td><td>${tag}</td></tr>`;
  }).join('');
  document.getElementById('d-table').innerHTML = `
    <thead><tr><th>Departamento</th><th>Categoría</th><th>Mes</th><th>Presupuesto</th><th>Ejecutado</th><th>% Ejecución</th><th>Estado</th></tr></thead>
    <tbody>${body}</tbody>`;
}

/* ---------- KPI card + chart option helpers ---------- */
function kpi(value,label,deltaClass){
  return `<div class="kpi"><div class="val">${value}</div><div class="lbl">${label}</div>${deltaClass?`<div class="delta ${deltaClass}">&nbsp;</div>`:''}</div>`;
}
function val(id){ return document.getElementById(id).value; }
function baseLineOpts(){
  return { responsive:true, maintainAspectRatio:false,
    plugins:{ legend:{position:'bottom',labels:{boxWidth:12,font:{size:11}}}, tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${fmtEUR2(c.raw)}`}} },
    scales:{ y:{ticks:{callback:v=>fmtCompactEUR(v)}}, x:{grid:{display:false}} } };
}
function baseBarOpts(){
  return { responsive:true, maintainAspectRatio:false,
    plugins:{ legend:{position:'bottom',labels:{boxWidth:12,font:{size:11}}}, tooltip:{callbacks:{label:c=>`${c.dataset.label||''}: ${fmtEUR2(c.raw)}`}} },
    scales:{ y:{ticks:{callback:v=>fmtCompactEUR(v)}}, x:{grid:{display:false}} } };
}

/* ============================================================
   BOOTSTRAP
   ============================================================ */
const RENDERERS = { resumen:renderResumen, ingresos:renderIngresos, gastos:renderGastos,
  presupuesto:renderPresupuesto, forecast:renderForecast, detalle:renderDetalle };

function buildPages(){
  const sk = skeletons();
  const container = document.getElementById('pages');
  container.innerHTML = PAGES.map(p=>`<div class="page" id="${p.id}">${sk[p.id]}</div>`).join('');
}

function wireFilters(pageId){
  document.querySelectorAll(`#${pageId} select, #${pageId} input`).forEach(el=>{
    el.addEventListener('change', ()=> RENDERERS[pageId]());
    el.addEventListener('keyup', ()=> RENDERERS[pageId]());
  });
}

function showPage(id){
  document.querySelectorAll('.navtabs button').forEach(b=>b.classList.toggle('active', b.dataset.page===id));
  document.querySelectorAll('.page').forEach(p=>p.classList.toggle('active', p.id===id));
  RENDERERS[id]();
}

function initNav(){
  const nav = document.getElementById('navtabs');
  nav.innerHTML = PAGES.map(p=>`<button data-page="${p.id}">${p.label}</button>`).join('');
  nav.querySelectorAll('button').forEach(btn=> btn.addEventListener('click', ()=> showPage(btn.dataset.page)));
}

document.addEventListener('DOMContentLoaded', ()=>{
  buildPages();
  initNav();
  PAGES.forEach(p=> wireFilters(p.id));
  showPage('resumen');
});
