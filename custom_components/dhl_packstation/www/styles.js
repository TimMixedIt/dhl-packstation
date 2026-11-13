export const styles = `
  :host { display:block; color:var(--primary-text-color,#f5f5f5); font-family:var(--paper-font-body1_-_font-family,Roboto,Arial,sans-serif); }
  * { box-sizing:border-box; }
  ha-card { display:block; overflow:hidden; background:var(--ha-card-background,var(--card-background-color,#191919)); border-radius:var(--ha-card-border-radius,12px); border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#333)); }
  button,input,select { font:inherit; }
  button { color:inherit; cursor:pointer; }
  button:disabled { cursor:default; }
  button:focus-visible,summary:focus-visible { outline:3px solid var(--primary-color,#03a9f4); outline-offset:3px; }
  summary { min-height:64px; display:flex; align-items:center; gap:16px; padding:16px 20px; cursor:pointer; font-weight:700; font-size:clamp(20px,4.2vw,24px); list-style:none; }
  summary::-webkit-details-marker { display:none; }
  .locker { width:28px; height:28px; color:var(--secondary-text-color,#aaa); flex-shrink:0; }
  .chevron { margin-left:auto; width:24px; height:24px; transition:transform .15s; }
  details[open] > summary .chevron { transform:rotate(180deg); }
  .body { padding:24px clamp(16px,4vw,48px) 28px; }
  .sizes-header { display:flex; align-items:center; justify-content:space-between; gap:12px; margin:12px 0 24px; }
  .sizes-header h2 { font-size:clamp(16px,3.5vw,20px); margin:0; }
  .info { display:grid; place-items:center; background:none; border:0; padding:4px; min-width:44px; min-height:44px; color:var(--secondary-text-color,#aaa); }
  .info svg { width:28px; height:28px; }
  .grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:clamp(8px,2vw,12px); }
  .tile { border:0; background:var(--secondary-background-color,#2d2d2d); border-radius:7px; min-width:0; height:clamp(160px,31vw,230px); padding:10px 8px; display:flex; flex-direction:column; align-items:center; gap:6px; text-align:center; }
  .state-icon { display:block; width:28px; height:28px; flex-shrink:0; }
  .yes { color:#89bd3d; } .neutral { color:var(--secondary-text-color,#aaa); }
  .shape-space { width:100%; flex:1; display:flex; align-items:flex-end; margin-top:8px; }
  .shape { width:100%; display:grid; place-items:center; font-weight:750; font-size:clamp(20px,4.5vw,28px); color:#171717; background:#fbd443; border:3px solid #ac9736; border-radius:6px; }
  .shape.s { height:25%; min-height:28px; } .shape.m { height:42%; } .shape.l { height:56%; } .shape.xl { height:90%; }
  .tile.unknown .shape,.tile.empty .shape { background:var(--disabled-color,#777); border-color:var(--secondary-text-color,#aaa); color:var(--card-background-color,#191919); }
  .tile.unknown .shape { background:transparent; color:var(--secondary-text-color,#aaa); border-style:dashed; }
  .count { font-size:clamp(12px,2.7vw,16px); line-height:1.2; font-weight:700; overflow-wrap:anywhere; }
  .timestamp { margin-top:24px; padding:12px; border-radius:6px; background:var(--secondary-background-color,#242424); color:var(--secondary-text-color,#aaa); font-size:14px; line-height:1.5; }
  .note { color:var(--secondary-text-color,#aaa); font-size:14px; line-height:1.5; margin:24px 0 0; }
  .warning { color:var(--warning-color,#e3b341); font-size:14px; margin:0 0 16px; line-height:1.5; }
  .empty-message { margin:0; padding:16px; font-size:15px; line-height:1.5; color:var(--secondary-text-color,#aaa); }
  .overview { padding:0 20px 20px; }
  .station { padding:20px 0; border-top:1px solid var(--divider-color,#444); }
  .station:last-of-type { padding-bottom:0; }
  .station-heading { display:flex; align-items:flex-start; justify-content:space-between; flex-wrap:wrap; gap:8px; }
  .station h2 { font-size:17px; margin:0; }
  .address { margin:6px 0 16px; color:var(--secondary-text-color,#aaa); font-size:13px; line-height:1.4; }
  .badge { font-size:11px; font-weight:650; padding:4px 8px; border-radius:4px; background:var(--secondary-background-color,#2d2d2d); }
  .badge.fresh { color:var(--success-color,#89bd3d); } .badge:not(.fresh) { color:var(--warning-color,#e3b341); }
  .metric { min-width:0; padding:10px 6px; background:var(--secondary-background-color,#2d2d2d); border:0; border-radius:6px; display:flex; flex-direction:column; align-items:center; gap:8px; }
  .metric-heading { display:flex; align-items:center; gap:6px; font-weight:750; color:#171717; background:#fbd443; padding:4px 7px; border-radius:4px; width:100%; justify-content:center; }
  .metric .state-icon { width:16px; height:16px; }
  .metric.unknown .metric-heading { color:var(--secondary-text-color,#aaa); background:transparent; outline:1px dashed currentColor; }
  .metric.empty .metric-heading { background:var(--disabled-color,#777); }
  .station .timestamp { background:none; padding:0; margin-top:12px; font-size:12px; }
  dialog { color:var(--primary-text-color,#eee); background:var(--ha-card-background,var(--card-background-color,#191919)); border:1px solid var(--divider-color,#555); border-radius:12px; padding:24px; width:min(420px,calc(100vw - 32px)); max-height:calc(100dvh - 48px); overflow:auto; }
  dialog::backdrop { background:rgba(0,0,0,.55); }
  dialog h2 { font-size:20px; margin:0 0 16px; } dialog p { font-size:15px; line-height:1.6; }
  .close { float:right; min-height:44px; padding:8px 16px; border:1px solid var(--divider-color,#555); border-radius:6px; color:var(--primary-text-color,#fff); background:var(--secondary-background-color,#333); }
  @media(max-width:360px) { .body { padding:8px 12px 20px; } summary { padding:16px; gap:12px; } .tile { padding:8px 5px; } .overview { padding:0 12px 16px; } }
  @media(prefers-reduced-motion:reduce) { .chevron { transition:none; } }
`;
