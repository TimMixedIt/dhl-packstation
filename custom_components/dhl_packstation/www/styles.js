export const styles = `
  :host { display:block; container-type:inline-size; color:var(--primary-text-color,#f5f5f5); font-family:var(--paper-font-body1_-_font-family,Roboto,Arial,sans-serif); }
  * { box-sizing:border-box; }
  ha-card { display:block; overflow:hidden; background:var(--ha-card-background,var(--card-background-color,#191919)); border-radius:var(--ha-card-border-radius,12px); border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#333)); }
  button,input,select { font:inherit; }
  button { appearance:none; color:inherit; cursor:pointer; }
  button:disabled { cursor:default; }
  button:focus-visible,summary:focus-visible { outline:3px solid var(--primary-color,#03a9f4); outline-offset:3px; }
  summary { min-height:clamp(52px,10.7cqw,64px); display:flex; align-items:center; gap:16px; padding:12px 20px; cursor:pointer; font-weight:700; font-size:clamp(20px,4.2cqw,24px); list-style:none; }
  summary::-webkit-details-marker { display:none; }
  .locker { width:28px; height:28px; color:var(--secondary-text-color,#aaa); flex-shrink:0; }
  .chevron { margin-left:auto; width:24px; height:24px; transition:transform .15s; }
  details[open] > summary .chevron { transform:rotate(180deg); }
  .body { padding:clamp(8px,4cqw,24px) clamp(12px,5.3cqw,32px) 24px; }
  .sizes-header { display:flex; align-items:center; justify-content:space-between; gap:12px; margin:0 0 clamp(12px,4cqw,24px); }
  .sizes-header h2 { font-size:clamp(16px,3.5cqw,20px); margin:0; }
  .info { display:grid; place-items:center; background:none; border:0; padding:4px; min-width:44px; min-height:44px; color:var(--secondary-text-color,#aaa); }
  .info svg { width:28px; height:28px; }
  .grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:clamp(8px,2cqw,12px); }
  .tile { border:0; background:var(--secondary-background-color,#2d2d2d); border-radius:7px; min-width:0; height:clamp(160px,38cqw,230px); padding:10px 8px; display:grid; grid-template-rows:28px minmax(0,1fr) 2.4em; justify-items:center; gap:6px; text-align:center; font-size:clamp(12px,2.7cqw,16px); line-height:1.2; }
  .state-icon { display:block; width:28px; height:28px; flex-shrink:0; }
  .yes { color:#89bd3d; } .neutral { color:var(--secondary-text-color,#aaa); }
  .shape-space { width:100%; height:100%; min-height:0; display:flex; align-items:flex-end; }
  .shape { width:100%; min-height:calc(1em + 8px); display:grid; place-items:center; font-weight:750; font-size:clamp(18px,4.8cqw,28px); line-height:1; color:#171717; background:#fbd443; border:3px solid #ac9736; border-radius:6px; }
  .shape.s { height:25%; } .shape.m { height:42%; } .shape.l { height:56%; } .shape.xl { height:90%; }
  .tile.unknown .shape,.tile.empty .shape { background:var(--disabled-color,#777); border-color:var(--secondary-text-color,#aaa); color:var(--card-background-color,#191919); }
  .tile.unknown .shape { background:transparent; color:var(--secondary-text-color,#aaa); border-style:dashed; }
  .count { font-size:clamp(12px,2.7cqw,16px); line-height:1.2; font-weight:700; overflow-wrap:anywhere; }
  .timestamp { margin-top:24px; padding:12px; border-radius:6px; background:var(--secondary-background-color,#242424); color:var(--secondary-text-color,#aaa); font-size:14px; line-height:1.5; }
  .note { color:var(--secondary-text-color,#aaa); font-size:14px; line-height:1.5; margin:24px 0 0; }
  .warning { color:var(--warning-color,#e3b341); font-size:14px; margin:0 0 16px; line-height:1.5; }
  .empty-message { margin:0; padding:16px; font-size:15px; line-height:1.5; color:var(--secondary-text-color,#aaa); }
  .station-summary { display:flex; justify-content:space-between; gap:8px; margin-top:12px; font-size:14px; }
  .station-summary a { color:var(--primary-color); }
  .week { border:1px solid var(--divider-color,#777); border-radius:12px; margin-top:16px; padding:12px; }
  .week h2 { font-size:16px; margin:0 0 8px; }
  .week ul { list-style:none; margin:0; padding:0; display:grid; grid-template-columns:repeat(7,minmax(0,1fr)); gap:4px; }
  .week li { display:grid; text-align:center; font-size:12px; gap:3px; background:var(--secondary-background-color,#333); border-radius:6px; padding:5px 0; }
  .trend-value { font-weight:700; font-size:14px; }
  .week li::after { content:""; justify-self:center; width:7px; height:7px; border-radius:50%; background:var(--trend-color,var(--disabled-color,#777)); }
  .week .many { --trend-color:var(--success-color,#6ca530); }
  .week .few { --trend-color:var(--warning-color,#d09121); }
  .week .none { --trend-color:var(--error-color,#db4448); }
  .week p { color:var(--secondary-text-color); font-size:12px; margin:8px 0 0; }
  .overview { padding:0 20px 20px; }
  .directions { display:flex; flex-wrap:wrap; gap:6px 12px; align-items:center; }
  .directions a { display:inline-flex; min-height:28px; align-items:center; }
  .compare { margin-top:14px; }
  .compare-row { display:grid; grid-template-columns:minmax(0,1fr) repeat(4,minmax(30px,9cqw)); align-items:center; gap:4px; }
  .compare-head { color:var(--secondary-text-color,#aaa); font-size:12px; font-weight:700; text-align:center; padding:0 0 4px; }
  .compare-head span:first-child { text-align:left; padding-left:4px; }
  .station { padding:5px 0; border-top:1px solid var(--divider-color,#444); }
  .station-toggle { position:relative; min-width:0; background:none; border:0; padding:5px 14px 5px 4px; text-align:left; min-height:44px; display:grid; gap:2px; }
  .station-name { font-size:14px; font-weight:700; overflow-wrap:anywhere; }
  .station-toggle::after { content:""; position:absolute; right:4px; top:10px; width:5px; height:5px; border:solid var(--secondary-text-color,#aaa); border-width:0 1.5px 1.5px 0; transform:rotate(45deg); }
  .station-toggle[aria-expanded="true"]::after { transform:rotate(225deg); top:13px; }
  .compare-label { color:var(--secondary-text-color,#aaa); font-size:12px; overflow-wrap:anywhere; }
  .compare-label.fits { color:var(--success-color,#89bd3d); font-weight:700; }
  .compare-label.shortage { font-weight:650; }
  .compare-result { font-size:14px; font-weight:700; margin:0 0 10px; }
  .metric { min-width:0; min-height:36px; padding:2px; border:0; border-radius:6px; font-size:13px; font-weight:650; background:var(--secondary-background-color,#2d2d2d); }
  .metric.available { background:#fbd443; color:#171717; }
  .metric.unknown,.metric.empty { color:var(--secondary-text-color,#aaa); }
  .station-detail { padding:0 4px 8px; }
  .address { margin:4px 0; color:var(--secondary-text-color,#aaa); font-size:13px; overflow-wrap:anywhere; }
  .station .timestamp { background:none; padding:0; margin-top:4px; font-size:12px; }
  .station .station-summary { margin-top:4px; }
  dialog { color:var(--primary-text-color,#eee); background:var(--ha-card-background,var(--card-background-color,#191919)); border:1px solid var(--divider-color,#555); border-radius:12px; padding:24px; width:min(420px,calc(100vw - 32px)); max-height:calc(100dvh - 48px); overflow:auto; }
  dialog::backdrop { background:rgba(0,0,0,.55); }
  dialog h2 { font-size:20px; margin:0 0 16px; } dialog p { font-size:15px; line-height:1.6; }
  .close { float:right; min-height:44px; padding:8px 16px; border:1px solid var(--divider-color,#555); border-radius:6px; color:var(--primary-text-color,#fff); background:var(--secondary-background-color,#333); }
  @container(max-width:360px) { .body { padding:8px 12px 20px; } summary { padding:12px 16px; gap:12px; } .tile { padding:8px 5px; } .overview { padding:0 12px 16px; } }
  @media(prefers-reduced-motion:reduce) { .chevron { transition:none; } }
`;
