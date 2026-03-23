<script lang="ts">
    interface Props {
        speed: number;
        pressure: number;
        temperatures: number[];
        getTempColor: (temp: number) => string;
    }

    let { speed, pressure, temperatures, getTempColor }: Props = $props();

    // Helper to determine the correct label based on the number of layers
    function getLayerLabel(index: number, total: number) {
        if (total === 1) return 'SURF';
        if (total === 2) return index === 0 ? 'SURF' : 'CORE';
        if (total === 3) {
            if (index === 0) return 'SURF';
            if (index === 1) return 'MID';
            return 'CORE';
        }
        return '';
    }
</script>

<div class="flex flex-col gap-1.5 w-28 shrink-0">
    
    <div class="grid grid-cols-2 gap-2 border-b border-zinc-800/80 pb-1.5">
        <div>
            <span class="text-[9px] font-bold text-zinc-600 uppercase block tracking-wider leading-none mb-0.5">Speed</span>
            <div class="font-mono text-xs font-bold text-white leading-none tabular-nums">
                {Math.round(speed)}<span class="text-[8px] text-zinc-500 font-normal ml-0.5">km/h</span>
            </div>
        </div>
        <div>
            <span class="text-[9px] font-bold text-zinc-600 uppercase block tracking-wider leading-none mb-0.5">Press</span>
            <div class="font-mono text-xs font-bold text-white leading-none tabular-nums">
                {pressure.toFixed(1)}<span class="text-[8px] text-zinc-500 font-normal ml-0.5">psi</span>
            </div>
        </div>
    </div>

<div>
        <span class="text-[9px] font-bold text-zinc-600 uppercase block tracking-wider leading-none mb-1.5">Temperatures</span>
        <div class="flex justify-between font-mono text-xs font-bold tabular-nums">
            {#each temperatures as temp, i}
                <div class="flex flex-col items-center">
                    <span class="text-[8px] text-zinc-500 mb-0.5 leading-none">{getLayerLabel(i, temperatures.length)}</span>
                    
                    <span style="color: {getTempColor(temp)}; text-shadow: 0 0 4px rgba(0,0,0,0.5);">
                        {Math.round(temp)}°
                    </span>
                </div>
            {/each}
        </div>
    </div>
</div>