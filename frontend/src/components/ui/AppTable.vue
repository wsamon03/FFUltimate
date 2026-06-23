<template>
  <div class="overflow-x-auto rounded-xl border" style="border-color: var(--color-border)">
    <table class="min-w-full text-sm">
      <thead style="background: var(--color-card)">
        <slot name="head" />
      </thead>
      <tbody style="background: var(--color-bg)">
        <slot />
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
// Intentionally empty — purely structural
</script>

<style>
/* Applied globally so slotted elements pick these up */
table {
  table-layout: fixed;
}

table th {
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

table td {
  padding: 0.75rem 1rem;
  color: var(--color-text-primary);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
  overflow: hidden;
}

table tbody tr:last-child td {
  border-bottom: none;
}

table tbody tr:hover td {
  background: var(--color-card-hover);
}

/* ── Stat group column tints ─────────────────────────────────
   Alternates between theme colors only:
     A = primary (blue)
     B = text-secondary (slate, desaturated)
     C = primary-hover (slightly darker/shifted blue)
     N = border (near-neutral, for fumbles)
   Offense:  pass=A  rush=B  rec=C  fum=N
   Defense:  tkl=A   cov=B   to=C
   Special:  kick=A  punt=B  ret=C
─────────────────────────────────────────────────────────── */
table th.col-pass, table td.col-pass { background: color-mix(in srgb, var(--color-primary) 8%, transparent) !important; }
table th.col-rush, table td.col-rush { background: color-mix(in srgb, var(--color-text-secondary) 8%, transparent) !important; }
table th.col-rec,  table td.col-rec  { background: color-mix(in srgb, var(--color-primary-hover) 10%, transparent) !important; }
table th.col-fum,  table td.col-fum  { background: color-mix(in srgb, var(--color-border) 25%, transparent) !important; }
table th.col-tkl,  table td.col-tkl  { background: color-mix(in srgb, var(--color-primary) 8%, transparent) !important; }
table th.col-cov,  table td.col-cov  { background: color-mix(in srgb, var(--color-text-secondary) 8%, transparent) !important; }
table th.col-to,   table td.col-to   { background: color-mix(in srgb, var(--color-primary-hover) 10%, transparent) !important; }
table th.col-kick, table td.col-kick { background: color-mix(in srgb, var(--color-primary) 8%, transparent) !important; }
table th.col-punt, table td.col-punt { background: color-mix(in srgb, var(--color-text-secondary) 8%, transparent) !important; }
table th.col-ret,  table td.col-ret  { background: color-mix(in srgb, var(--color-primary-hover) 10%, transparent) !important; }

/* Slightly brighter tint on hover for grouped columns */
table tbody tr:hover td.col-pass { background: color-mix(in srgb, var(--color-primary) 14%, transparent) !important; }
table tbody tr:hover td.col-rush { background: color-mix(in srgb, var(--color-text-secondary) 14%, transparent) !important; }
table tbody tr:hover td.col-rec  { background: color-mix(in srgb, var(--color-primary-hover) 16%, transparent) !important; }
table tbody tr:hover td.col-fum  { background: color-mix(in srgb, var(--color-border) 35%, transparent) !important; }
table tbody tr:hover td.col-tkl  { background: color-mix(in srgb, var(--color-primary) 14%, transparent) !important; }
table tbody tr:hover td.col-cov  { background: color-mix(in srgb, var(--color-text-secondary) 14%, transparent) !important; }
table tbody tr:hover td.col-to   { background: color-mix(in srgb, var(--color-primary-hover) 16%, transparent) !important; }
table tbody tr:hover td.col-kick { background: color-mix(in srgb, var(--color-primary) 14%, transparent) !important; }
table tbody tr:hover td.col-punt { background: color-mix(in srgb, var(--color-text-secondary) 14%, transparent) !important; }
table tbody tr:hover td.col-ret  { background: color-mix(in srgb, var(--color-primary-hover) 16%, transparent) !important; }

/* Left-border divider at the start of each group */
table th.col-divider, table td.col-divider {
  border-left: 2px solid color-mix(in srgb, var(--color-border) 60%, transparent) !important;
}
table th.col-pass.col-divider, table td.col-pass.col-divider { border-left-color: color-mix(in srgb, var(--color-primary) 50%, transparent) !important; }
table th.col-rush.col-divider, table td.col-rush.col-divider { border-left-color: color-mix(in srgb, var(--color-text-secondary) 50%, transparent) !important; }
table th.col-rec.col-divider,  table td.col-rec.col-divider  { border-left-color: color-mix(in srgb, var(--color-primary-hover) 50%, transparent) !important; }
table th.col-fum.col-divider,  table td.col-fum.col-divider  { border-left-color: color-mix(in srgb, var(--color-border) 70%, transparent) !important; }
table th.col-tkl.col-divider,  table td.col-tkl.col-divider  { border-left-color: color-mix(in srgb, var(--color-primary) 50%, transparent) !important; }
table th.col-cov.col-divider,  table td.col-cov.col-divider  { border-left-color: color-mix(in srgb, var(--color-text-secondary) 50%, transparent) !important; }
table th.col-to.col-divider,   table td.col-to.col-divider   { border-left-color: color-mix(in srgb, var(--color-primary-hover) 50%, transparent) !important; }
table th.col-kick.col-divider, table td.col-kick.col-divider { border-left-color: color-mix(in srgb, var(--color-primary) 50%, transparent) !important; }
table th.col-punt.col-divider, table td.col-punt.col-divider { border-left-color: color-mix(in srgb, var(--color-text-secondary) 50%, transparent) !important; }
table th.col-ret.col-divider,  table td.col-ret.col-divider  { border-left-color: color-mix(in srgb, var(--color-primary-hover) 50%, transparent) !important; }

/* ── Group header spanning row ────────────────────────────── */
table th.col-group-anchor {
  border-bottom: none !important;
  background: var(--color-card) !important;
}
table th.col-group-label {
  text-align: center !important;
  font-size: 0.6rem !important;
  letter-spacing: 0.12em !important;
  font-weight: 700 !important;
  padding: 0.3rem 0.5rem !important;
  border-bottom: none !important;
}
table th.col-group-pass { background: color-mix(in srgb, var(--color-primary) 25%, transparent) !important; color: color-mix(in srgb, var(--color-primary) 60%, white) !important; }
table th.col-group-rush { background: color-mix(in srgb, var(--color-text-secondary) 20%, transparent) !important; color: var(--color-text-secondary) !important; }
table th.col-group-rec  { background: color-mix(in srgb, var(--color-primary-hover) 28%, transparent) !important; color: color-mix(in srgb, var(--color-primary-hover) 60%, white) !important; }
table th.col-group-fum  { background: color-mix(in srgb, var(--color-border) 40%, transparent) !important; color: var(--color-text-secondary) !important; }
table th.col-group-tkl  { background: color-mix(in srgb, var(--color-primary) 25%, transparent) !important; color: color-mix(in srgb, var(--color-primary) 60%, white) !important; }
table th.col-group-cov  { background: color-mix(in srgb, var(--color-text-secondary) 20%, transparent) !important; color: var(--color-text-secondary) !important; }
table th.col-group-to   { background: color-mix(in srgb, var(--color-primary-hover) 28%, transparent) !important; color: color-mix(in srgb, var(--color-primary-hover) 60%, white) !important; }
table th.col-group-kick { background: color-mix(in srgb, var(--color-primary) 25%, transparent) !important; color: color-mix(in srgb, var(--color-primary) 60%, white) !important; }
table th.col-group-punt { background: color-mix(in srgb, var(--color-text-secondary) 20%, transparent) !important; color: var(--color-text-secondary) !important; }
table th.col-group-ret  { background: color-mix(in srgb, var(--color-primary-hover) 28%, transparent) !important; color: color-mix(in srgb, var(--color-primary-hover) 60%, white) !important; }
</style>
