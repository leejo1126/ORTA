const fs = require('fs');
const path = require('path');
// Reproducible, location-independent paths. Inputs are committed under generate/inputs/;
// outputs are the curated design keepers under the experiment's results/ tier.
// Regenerate with:  node generate/build.js   (from the experiment dir, or anywhere).
const SP = path.join(__dirname, 'inputs');
const OUT = path.join(__dirname, '..', 'results');
fs.mkdirSync(OUT, {recursive:true});
const HALF = 5000;      // DNA half-window for promoters (TSS +/- 5kb)
const MIN_ENH = 10000;  // enhancer windows < this are expanded to 10kb (centered); 10-20kb kept as-is
const SKIP_RNA = new Set([]); // (E_Cd9 given an eRNA probe for symmetry) — DNA-only features go here
function W(path,data){ try{ fs.writeFileSync(path,data); } catch(e){ console.log('  !! SKIPPED (locked): '+path.split('/').pop()); } }

// ---- read sheet
const feats = fs.readFileSync(SP+'/sheet_clean.tsv','utf8').trim().split(/\r?\n/).map(l=>{
  const [name,chr,start,end,strand] = l.split('\t');
  return {name, chr, start:+start, end:+end, strand, type: name.startsWith('P_')?'P':'E'};
});

// ---- source coordinate corrections
// Ski locus typo: 151 Mb -> 155 Mb (+4,000,000) for E1_Ski, E2_Ski, P_Ski
for (const f of feats){ if(/_Ski$/.test(f.name)){ f.start+=4000000; f.end+=4000000; f.corr='+4Mb (151->155 typo)'; } }

// ---- Cd9 simplification: drop E1/E2/E3 individual + shared-readout scheme; keep ONE large enhancer over the cluster
const cd9drop=new Set(['E1_Cd9','E2_Cd9','E3_Cd9']);
for(let i=feats.length-1;i>=0;i--) if(cd9drop.has(feats[i].name)) feats.splice(i,1);
feats.push({name:'E_Cd9', chr:'chr6', start:125407000, end:125437000, strand:'+', type:'E',
  corr:'single large enhancer over cluster (dropped E1/E2/E3 + shared readout)'});

// ---- NEW functionally-validated pairs (see literature wiki: Klf4=[[xie-2017-klf4]], Car2=[[hansen-2025-adt4221]])
feats.push(
  {name:'E_Klf4',  chr:'chr4', start:55460173, end:55482053, strand:'+', type:'E', src:'Klf4 E1(69kb,-70%)+E2(55kb,-85%) contiguous ~22kb; E1/E2 resolvable via staged plate-3/4 sub-readouts'},
  {name:'P_Klf4',  chr:'chr4', start:55522466, end:55532466, strand:'-', type:'P', src:'Klf4 mRNA body [TSS-10k,TSS]'},
  {name:'E1_Car2', chr:'chr3', start:14993359, end:15001758, strand:'+', type:'E', src:'Car2 proximal enh ~107kb (Hansen)'},
  {name:'E2_Car2', chr:'chr3', start:15054523, end:15057481, strand:'+', type:'E', src:'Car2 distal enh ~168kb (Hansen)'},
  {name:'P_Car2',  chr:'chr3', start:14886428, end:14896428, strand:'+', type:'P', src:'Car2 mRNA body [TSS,TSS+10k]'},
  // Hansen supp additions (2026-07-17). Enhancers <10kb auto-expanded by the sizing rule below.
  {name:'P_Inhbb',   chr:'chr1',  start:119412248, end:119422248, strand:'-', type:'P', src:'Inhbb (Hansen); mRNA body [TSS-10k,TSS]'},
  {name:'E1_Inhbb',  chr:'chr1',  start:119141589, end:119150098, strand:'+', type:'E', src:'Inhbb distal enh ~276kb (Hansen)'},
  {name:'E2_Inhbb',  chr:'chr1',  start:119297289, end:119309265, strand:'-', type:'E', src:'Inhbb enh ~119kb (Hansen)'},
  {name:'P_Ceacam1', chr:'chr7',  start:25467534,  end:25477534,  strand:'-', type:'P', src:'Ceacam1 (Hansen); mRNA body [TSS-10k,TSS]'},
  {name:'E_Ceacam1', chr:'chr7',  start:25431053,  end:25439077,  strand:'-', type:'E', src:'Ceacam1 enh ~42kb (Hansen); - strand avoids + lncRNA'},
  {name:'P_Zbtb10',  chr:'chr3',  start:9250602,   end:9260602,   strand:'+', type:'P', src:'Zbtb10 (Hansen); mRNA body [TSS,TSS+10k]'},
  {name:'E_Zbtb10',  chr:'chr3',  start:9080721,   end:9084329,   strand:'-', type:'E', src:'Zbtb10 enh ~168kb (Hansen)'},
  {name:'P_Prdm14',  chr:'chr1',  start:13117163,  end:13127163,  strand:'-', type:'P', src:'Prdm14 (Hansen); mRNA body [TSS-10k,TSS]'},
  {name:'E_Prdm14',  chr:'chr1',  start:13082457,  end:13097137,  strand:'+', type:'E', src:'Prdm14 enh ~37kb (Hansen)'},
  {name:'P_Sik1',    chr:'chr17', start:31845792,  end:31855792,  strand:'-', type:'P', src:'Sik1 (Hansen); mRNA body [TSS-10k,TSS]; shares E_Rrp1b'},
);

// ---- DROP: low/no-FISH-signal Novo-2018 (correlative) pairs, to fit the 5 new validated pairs in 96/96 (2026-07-17)
const DROP = new Set(['E_Myb','P_Myb','E_Sox15','P_Senp3','E_Srxn1','P_Srxn1','E1_Ski','E2_Ski','P_Ski']);
for(let i=feats.length-1;i>=0;i--) if(DROP.has(feats[i].name)) feats.splice(i,1);

// ---- read chosen promoter TSS
const tssMap = {};
fs.readFileSync(SP+'/promoter_tss_chosen.tsv','utf8').trim().split(/\r?\n/).forEach(l=>{
  const [name,chr,strand,edge,tss,enstrand]=l.split('\t');
  tssMap[name]={tss:+tss, enstrand};
});

// ---- manual overrides for the 4 flagged promoters
const override = {
  'P_mir290': {tss:3218626, strand:'+', note:'PROVISIONAL: pri-miR-290 cluster start (Mir290a); no Ensembl TSS'},
  'P_Ski':    {tss:155222535, note:'COORD FIX +4Mb (151->155 typo); Ski-001 TSS'},
  'P_Ddx11':  {tss:66123520, strand:'+', note:'STRAND FIX: Ensembl Ddx11 is + (sheet said -); TSS=window start; RNA strand also flips to +'},
  'P_Sall1':  {tss:89044162, rnaS:89034162, rnaE:89044162, note:'FIX: - strand gene body; RNA moved to [TSS-10kb,TSS], DNA re-centered on TSS'},
  'P_Klf4':   {tss:55532466, note:'NEW pair; Klf4 TSS 55,532,466 (-); RNA=mRNA body [TSS-10k,TSS]'},
  'P_Car2':   {tss:14886428, note:'NEW pair; Car2 TSS 14,886,428 (+); RNA=mRNA body [TSS,TSS+10k]'},
  'P_Inhbb':  {tss:119422248, note:'NEW (Hansen); Inhbb TSS 119,422,248 (-)'},
  'P_Ceacam1':{tss:25477534,  note:'NEW (Hansen); Ceacam1 TSS 25,477,534 (-)'},
  'P_Zbtb10': {tss:9250602,   note:'NEW (Hansen); Zbtb10 TSS 9,250,602 (+)'},
  'P_Prdm14': {tss:13127163,  note:'NEW (Hansen); Prdm14 TSS 13,127,163 (-)'},
  'P_Sik1':   {tss:31855792,  note:'NEW (Hansen); Sik1 TSS 31,855,792 (-) chr17; shares E_Rrp1b'},
};

// ---- build regions
for (const f of feats){
  f.note='';
  if (f.type==='E'){
    let s=f.start, e=f.end;
    if ((e-s) < MIN_ENH){ const c=Math.round((s+e)/2); s=c-HALF; e=c+HALF; f.resized=(f.end-f.start); }
    f.rnaS=s; f.rnaE=e; f.dnaS=s; f.dnaE=e; f.tssUsed=''; f.tssOff='';
    const n=[]; if(f.corr) n.push('COORD FIX: '+f.corr); if(f.src) n.push(f.src);
    if(f.resized!==undefined) n.push('window expanded '+f.resized+'bp->10kb');
    f.note=n.join('; ');
    continue;
  }
  // promoter
  f.rnaS=f.start; f.rnaE=f.end;                 // RNA unchanged (gene body)
  let tss = tssMap[f.name] ? tssMap[f.name].tss : null;
  let ens = tssMap[f.name] ? tssMap[f.name].enstrand : f.strand;
  if (override[f.name]){ const o=override[f.name];
    if(o.tss!==undefined) tss=o.tss;
    if(o.strand) f.strand=o.strand;
    if(o.rnaS!==undefined) f.rnaS=o.rnaS;
    if(o.rnaE!==undefined) f.rnaE=o.rnaE;
    f.note=o.note; }
  if (tss===null){ f.dnaS=f.start; f.dnaE=f.end; f.tssUsed='NA'; f.tssOff=''; continue; }
  f.tssUsed=tss;
  const edge = (f.strand==='+')?f.start:f.end;
  f.tssOff = tss-edge;
  f.dnaS = tss-HALF; f.dnaE = tss+HALF;
}

// ---- RNA-skip note (Cd9 individual enhancers: no validated eRNA)
for(const f of feats){ if(SKIP_RNA.has(f.name)) f.note=(f.note?f.note+'; ':'')+'RNA skipped (no validated eRNA)'; }

// ---- write coordinate table
const hdr=['name','type','chr','strand','rna_probe','rna_start','rna_end','dna_start','dna_end','tss_used','tss_offset','note'];
const rows=feats.map(f=>[f.name,f.type,f.chr,f.strand,SKIP_RNA.has(f.name)?'no':'yes',f.rnaS,f.rnaE,f.dnaS,f.dnaE,f.tssUsed,f.tssOff,f.note]);
W(OUT+'/coordinates_v2.csv',[hdr.join(','),...rows.map(r=>r.map(x=>{
  const s=String(x); return /[,"]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;}).join(','))].join('\n'));

// ---- DNA overlap detection (same chr, dna intervals intersect)
const ov=[];
for(let i=0;i<feats.length;i++)for(let j=i+1;j<feats.length;j++){
  const a=feats[i],b=feats[j];
  if(a.chr!==b.chr) continue;
  const s=Math.max(a.dnaS,b.dnaS), e=Math.min(a.dnaE,b.dnaE);
  if(s<e) ov.push({a:a.name,b:b.name,chr:a.chr,ovS:s,ovE:e,bp:e-s,ta:a.type,tb:b.type});
}
ov.sort((x,y)=>y.bp-x.bp);
W(OUT+'/dna_overlaps_v2.csv',
  ['featA,typeA,featB,typeB,chr,overlap_start,overlap_end,overlap_bp',
   ...ov.map(o=>[o.a,o.ta,o.b,o.tb,o.chr,o.ovS,o.ovE,o.bp].join(','))].join('\n'));

// ---- readout scheme
// round-robin by chromosome to keep consecutive rounds on different chr
function roundRobin(list){
  const byChr={}; for(const f of list){(byChr[f.chr]=byChr[f.chr]||[]).push(f);}
  // sort each chr group by position for determinism
  for(const c in byChr) byChr[c].sort((a,b)=>a.rnaS-b.rnaS);
  // order chromosomes by descending group size so big groups get spread
  let chrs=Object.keys(byChr).sort((a,b)=>byChr[b].length-byChr[a].length);
  const out=[]; let last=null; let remaining=list.length;
  while(remaining>0){
    // pick chr != last with most remaining
    let pick=null;
    const avail=chrs.filter(c=>byChr[c].length>0);
    const notLast=avail.filter(c=>c!==last);
    const pool=notLast.length?notLast:avail;
    pool.sort((a,b)=>byChr[b].length-byChr[a].length);
    pick=pool[0];
    out.push(byChr[pick].shift()); last=pick; remaining--;
  }
  return out;
}
const pinnedNames=['P_Hes1','P_Cd9','P_Klf3','P_Neat1']; // order: earlier..last (Neat1 last)
const enh=feats.filter(f=>f.type==='E');
const proAll=feats.filter(f=>f.type==='P');
const pinned=pinnedNames.map(n=>proAll.find(f=>f.name===n));
const proRest=proAll.filter(f=>!pinnedNames.includes(f.name));
const order=[...roundRobin(enh), ...roundRobin(proRest), ...pinned];

// assign readout numbers. RNA: 89 features (Cd9 enhancers skipped) -> 1..89
// DNA: all 92 features -> 97..188 (next 96-well plate) + Cd9 shared as final DNA round (189)
const rnaOrder = order.filter(f=>!SKIP_RNA.has(f.name));
const Nrna = rnaOrder.length;
const dnaStart = Math.ceil(Nrna/96)*96 + 1;      // 97
const dnaOrderIdx={}; order.forEach((f,i)=>dnaOrderIdx[f.name]=i);
const dnaReadout = name => dnaStart + dnaOrderIdx[name];
const plateOf = r => Math.ceil(r/96);
const scheme=[];
rnaOrder.forEach((f,i)=> scheme.push({round:i+1, block:'RNA', readout:i+1, feature:'RNA_'+f.name, type:f.type, chr:f.chr}));
order.forEach((f,i)=> scheme.push({round:Nrna+i+1, block:'DNA', readout:dnaReadout(f.name), feature:'DNA_'+f.name, type:f.type, chr:f.chr}));

// ---- staged Klf4 E1/E2 sub-region readouts (parked on plates 3=RNA / 4=DNA)
const KLF4_SUB=[
  {sub:'E1_Klf4', zs:55460173, ze:55470173, rna:193, dna:289, note:'69kb enh (-70%)'},
  {sub:'E2_Klf4', zs:55472053, ze:55482053, rna:194, dna:290, note:'55kb enh (-85%)'},
];
KLF4_SUB.forEach(k=>{
  scheme.push({round:'', block:'RNA-sub', readout:k.rna, feature:'RNA_'+k.sub, type:'E', chr:'chr4'});
  scheme.push({round:'', block:'DNA-sub', readout:k.dna, feature:'DNA_'+k.sub, type:'E', chr:'chr4'});
});
W(OUT+'/readout_scheme_v2.csv',
  ['imaging_round,block,plate,readout_number,feature,type,chr',
   ...scheme.map(s=>[s.round,s.block,plateOf(s.readout),s.readout,s.feature,s.type,s.chr].join(','))].join('\n'));

// ---- dual-barcode designations: a probe in the named zone carries primary + secondary readout (fiducial slot)
// carrier = feature whose probes carry both readouts in the zone; partner_action=drop means the
// partner feature's probes that fall in this zone are discarded (avoids double-tiling the overlap).
const dual=[];
// (a) 5 proximal E-P DNA overlaps -> secondary = partner's main DNA readout (plate 2)
ov.filter(o=>o.ta!==o.tb).forEach(o=>{
  dual.push({zone:'overlap', modality:'DNA', carrier:o.a, partner:o.b, partnerAction:'drop', chr:o.chr, start:o.ovS, end:o.ovE,
    primary:dnaReadout(o.a), secondary:dnaReadout(o.b),
    desc:o.a+'=A+B in overlap; '+o.b+' probes in zone dropped; flanks = readout+fiducial'});
});
// (b) staged Klf4 E1/E2 sub-regions -> secondary parked on plate 3 (RNA) / plate 4 (DNA); no drop (sub not separately tiled)
const klf4Rna = 1 + rnaOrder.findIndex(f=>f.name==='E_Klf4');
const klf4Dna = dnaReadout('E_Klf4');
KLF4_SUB.forEach(k=>{
  dual.push({zone:'staged-Klf4', modality:'DNA', carrier:'E_Klf4', partner:k.sub, partnerAction:'none', chr:'chr4', start:k.zs, end:k.ze,
    primary:klf4Dna, secondary:k.dna, desc:k.note+'; E_Klf4 DNA zone: contiguous '+klf4Dna+' + sub '+k.dna+' (plate 4)'});
  dual.push({zone:'staged-Klf4', modality:'RNA', carrier:'E_Klf4', partner:k.sub, partnerAction:'none', chr:'chr4', start:k.zs, end:k.ze,
    primary:klf4Rna, secondary:k.rna, desc:k.note+'; E_Klf4 RNA zone: contiguous '+klf4Rna+' + sub '+k.rna+' (plate 3)'});
});
W(OUT+'/dual_barcode_v2.csv',
  ['zone,modality,carrier,partner,partner_action,chr,region_start,region_end,readout_primary,plate_primary,readout_secondary,plate_secondary,description',
   ...dual.map(d=>[d.zone,d.modality,d.carrier,d.partner,d.partnerAction,d.chr,d.start,d.end,d.primary,plateOf(d.primary),d.secondary,plateOf(d.secondary),'"'+d.desc+'"'].join(','))].join('\n'));

// ---- hubs for BED coloring: group by gene token; a promoter-only ("orphan") group attaches to the
// nearest enhancer-bearing group on the same chr within GAP (so shared-enhancer hubs merge — Sik1->Rrp1b,
// Ddx11/Ankrd12->Mtcl1 — but two COMPLETE pairs that are merely genomically proximal keep distinct colors,
// e.g. Inhbb vs Tcfcp2l1).
const GAP=750000;
const tokenOf = nm => nm.replace(/^(E|P)\d*_/,'');
function hsl2rgb(h,s,l){ h/=360; const a=s*Math.min(l,1-l);
  const f=n=>{const k=(n+h*12)%12; return Math.round(255*(l-a*Math.max(-1,Math.min(k-3,9-k,1))));};
  return [f(0),f(8),f(4)]; }
const grp={};
feats.forEach(f=>{ const t=tokenOf(f.name); const c=(f.rnaS+f.rnaE)/2;
  const g=grp[t]||(grp[t]={token:t,chr:f.chr,hasE:false,lo:Infinity,hi:-Infinity});
  if(f.type==='E') g.hasE=true; g.lo=Math.min(g.lo,c); g.hi=Math.max(g.hi,c); });
const groups=Object.values(grp), complete=groups.filter(g=>g.hasE);
const hubKey={}; groups.forEach(g=>hubKey[g.token]=g.token);        // default: own token
groups.filter(g=>!g.hasE).forEach(o=>{                              // orphan promoter -> nearest enhancer group
  let best=null,bd=Infinity;
  complete.filter(c=>c.chr===o.chr).forEach(c=>{ const d=Math.max(0, Math.max(o.lo,c.lo)-Math.min(o.hi,c.hi)); if(d<bd){bd=d;best=c;} });
  if(best && bd<=GAP) hubKey[o.token]=best.token; });
const hubTokens=[...new Set(Object.values(hubKey))];
const hubColor={}; hubTokens.forEach((t,i)=>{const [r,g,b]=hsl2rgb((i*137.508)%360,0.62,0.48); hubColor[t]=r+','+g+','+b;});
const hubOf={}; const hubMap={};
feats.forEach(f=>{ const hk=hubKey[tokenOf(f.name)];
  hubOf[f.name]={rgb:hubColor[hk],label:hk};
  (hubMap[hk]=hubMap[hk]||[]).push(f.name); });
const hubMeta=Object.keys(hubMap).map(k=>({label:k,n:hubMap[k].length,members:hubMap[k].join('|')}));

// ---- BED (0-based) : one entry per RNA region and per DNA region, colored by hub
const bedLines=['track name="EP_ORCA_v2" description="RNA+DNA targets, colored by E-P hub" itemRgb="On" visibility=2'];
for(const f of feats){
  const col=hubOf[f.name].rgb;
  // DNA
  bedLines.push([f.chr,f.dnaS-1,f.dnaE,'DNA_'+f.name,0,f.strand,f.dnaS-1,f.dnaE,col].join('\t'));
  // RNA
  bedLines.push([f.chr,f.rnaS-1,f.rnaE,'RNA_'+f.name,0,f.strand,f.rnaS-1,f.rnaE,col].join('\t'));
}
W(OUT+'/ep_orca_v2.bed',bedLines.join('\n'));

// ---- console summary
const dnaEnd=dnaStart+order.length-1;
console.log('features:',feats.length,' enh:',enh.length,' prom:',proAll.length);
console.log('RNA readouts: 1..'+Nrna+'  (DNA-only skipped: '+([...SKIP_RNA].join(',')||'none')+')');
console.log('DNA readouts: '+dnaStart+'..'+dnaEnd+'  ('+order.length+' features)');
console.log('per 96-plate: RNA='+Nrna+' wells, DNA='+order.length+' wells  ('+(Math.max(Nrna,order.length)<=96?'both <=96 OK':'>96 !!')+')');
console.log('\nEnhancers resized (<10kb -> 10kb):');
feats.filter(f=>f.resized!==undefined).forEach(f=>console.log(`  ${f.name}: was ${f.resized}bp`));
console.log('\nDNA overlaps (dual-barcode zones):');
ov.filter(o=>o.ta!==o.tb).forEach(o=>console.log(`  ${o.a} x ${o.b}  ${o.chr}:${o.ovS}-${o.ovE}  ${o.bp}bp`));
const ovSame=ov.filter(o=>o.ta===o.tb); if(ovSame.length){ console.log('  [same-type overlaps]:'); ovSame.forEach(o=>console.log(`  ${o.a} x ${o.b}  ${o.bp}bp`)); }
console.log('\nStaged Klf4 sub-readouts (plate3=RNA / plate4=DNA): E_Klf4 contiguous = RNA '+klf4Rna+' / DNA '+klf4Dna);
KLF4_SUB.forEach(k=>console.log(`  ${k.sub} [${k.zs}-${k.ze}] -> RNA ${k.rna}(p${plateOf(k.rna)}) / DNA ${k.dna}(p${plateOf(k.dna)})`));
console.log('\nNEW features:', feats.filter(f=>/Klf4|Car2|^E_Cd9/.test(f.name)).map(f=>f.name).join(', '));
console.log('\nRNA imaging order:');
console.log(rnaOrder.map((f,i)=>`${i+1}:${f.name}`).join('  '));
console.log('\nPinned last:', pinnedNames.join(' -> '));
console.log('\nHubs ('+hubMeta.length+', multi-feature):');
hubMeta.filter(h=>h.n>1).forEach(h=>console.log(`  ${h.label} (${h.n}): ${h.members}`));
