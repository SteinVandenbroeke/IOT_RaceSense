<script lang="ts">
    import type { Circuit } from './circuit';

    let { activeCircuit }: { activeCircuit: Circuit } = $props();
</script>

<div class="flex flex-wrap items-end justify-between gap-4 mt-auto border-t border-zinc-800/50 pt-3">
    <div class="flex gap-6 md:gap-8">
        <div>
            <span class="text-[9px] font-bold text-zinc-600 uppercase block tracking-wider">Length</span>
            <span class="text-zinc-300 font-mono text-xs">{activeCircuit.lengthKm} km</span>
        </div>
        <div>
            <span class="text-[9px] font-bold text-zinc-600 uppercase block tracking-wider">Turns</span>
            <span class="text-zinc-300 font-mono text-xs">{activeCircuit.corners}</span>
        </div>
    </div>
    
    <div class="text-left md:text-right">
        <span class="text-[9px] font-bold text-zinc-600 uppercase block tracking-wider md:flex md:justify-end md:gap-1">
            Lap Record <span class="text-zinc-700">({activeCircuit.lapRecord.year})</span>
        </span>
        <div class="flex items-baseline justify-start md:justify-end gap-2">
            <span class="text-emerald-400 font-mono text-xs font-bold">{activeCircuit.lapRecord.time}</span>
            <span class="text-zinc-500 font-mono text-[10px] truncate">{activeCircuit.lapRecord.driver}</span>
        </div>
    </div>
</div>