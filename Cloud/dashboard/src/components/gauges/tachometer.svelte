<script lang="ts">
    export type BarRange = { min: number; max: number; colorClass: string };
    
    let unit = "rpm";
    
    interface Props {
        value: number;
        min?: number;
        max: number;
        stepSize?: number; // New: To determine how often to place a number marker
        segments?: number;
        ranges?: BarRange[];
        demo?: boolean;
    }

    let {
        value,
        min = 0,
        max,
        stepSize = 1, // Defaulting to 1 (e.g., 1, 2, 3, 4 for RPM x1000)
        segments = 40,
        ranges = [],
        demo = false
    }: Props = $props();

    // --- Demo Animation Logic ---
    let time = $state(0);
    let inc = Math.random() * 0.002 + 0.005;

    $effect(() => {
        if (!demo) return;
        
        const interval = setInterval(() => {
            time += inc; 
        }, 20);

        return () => clearInterval(interval);
    });

    let demoMultiplier = $derived((Math.sin(time) + 1) / 2);
    let displayValue = $derived(demo ? min + (demoMultiplier * (max - min)) : value);

    // --- Value Math ---
    let clampedValue = $derived(Math.max(min, Math.min(max, displayValue)));

    function getSegmentColor(val: number, isActive: boolean) {
        if (!isActive) return 'bg-zinc-800/50';
        
        if (ranges.length > 0) {
            const activeRange = ranges.find(r => val >= r.min && val <= r.max);
            if (activeRange) return activeRange.colorClass;
        }
        return 'bg-zinc-300';
    }
    
    // Calculate how many markers to generate based on the min, max, and stepSize
    let markerCount = $derived(Math.floor((max - min) / stepSize));
</script>

<article class="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col justify-center shadow-lg w-full h-full">    
    <div class="flex flex-col sm:flex-row sm:items-center gap-4 w-full">
        
        <div class="flex flex-col flex-1 w-full gap-1">
            <div class="flex items-center gap-[2px] h-6 w-full">
                {#each Array(segments) as _, i}
                    {@const segmentVal = min + (i / segments) * (max - min)}
                    {@const isActive = clampedValue > segmentVal}
                    {@const color = getSegmentColor(segmentVal, isActive)}
                    
                    <div class="flex-1 h-full rounded-[1px] -skew-x-12 transition-colors duration-100 {color}"></div>
                {/each}
            </div>

            <div class="relative w-full h-3">
                {#each Array(markerCount + 1) as _, i}
                    {@const val = min + (i * stepSize)}
                    {@const percent = ((val - min) / (max - min)) * 100}
                    
                    <span 
                        class="absolute top-0 -translate-x-1/2 text-[9px] font-mono text-zinc-500 font-bold"
                        style="left: {percent}%;"
                    >
                        {val}
                    </span>
                {/each}
            </div>
        </div>

<div class="flex items-baseline justify-end gap-2 shrink-0 w-32">
            
            <data 
                value={clampedValue.toString()} 
                class="w-16 text-right text-3xl font-mono font-black text-white tracking-tighter leading-none"
            >
                {clampedValue.toFixed(0)} 
            </data>

            <span class="text-zinc-500 font-mono text-xl leading-tight text-left">
                {unit}
            </span>
            
        </div>
        
    </div>
</article>