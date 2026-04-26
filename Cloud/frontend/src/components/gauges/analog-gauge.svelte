<script lang="ts">
    export type GaugeRange = { min: number; max: number; colorClass: string };

    interface Props {
        value: number;
        min?: number;
        max: number;
        unit: string;
        stepSize?: number; 
        intermediateTicks?: number; 
        precision?: number;
        ranges?: GaugeRange[];
        demo?: boolean; // New prop to trigger the sweep animation
    }

    let {
        value,
        min = 0,
        max,
        unit,
        stepSize = 10,
        intermediateTicks = 1,
        precision = 0,
        ranges = [],
        demo = false
    }: Props = $props();

    // --- Demo Animation Logic ---
    let time = $state(0);
    let inc = Math.random() * 0.002 + 0.005;
    $effect(() => {
        if (!demo) return;
        
        // Runs a 50fps loop to increment time
        const interval = setInterval(() => {
            // Speed of the sweep (lower is slower)
            time += inc; 
        }, 20);

        return () => clearInterval(interval);
    });

    // Math.sin(time) goes from -1 to 1. We map it to 0 to 1.
    let demoMultiplier = $derived((Math.sin(time) + 1) / 2);
    
    // Determine which value to display and calculate against
    let displayValue = $derived(demo ? min + (demoMultiplier * (max - min)) : value);

    // --- Gauge Math ---
    let clampedValue = $derived(Math.max(min, Math.min(max, displayValue)));
    
    let scaleMax = $derived(Math.ceil((max - min) / stepSize) * stepSize + min);

    let needleAngle = $derived(-135 + ((clampedValue - min) / (scaleMax - min)) * 270);
    let trackEndAngle = $derived(-135 + ((max - min) / (scaleMax - min)) * 270);

    let subdivisions = $derived(intermediateTicks + 1);
    let totalTicks = $derived(((scaleMax - min) / stepSize) * subdivisions);

    function getTickColorClass(val: number, isMajor: boolean) {
        if (ranges.length > 0) {
            const activeRange = ranges.find(r => val >= r.min && val <= r.max);
            if (activeRange) return activeRange.colorClass;
        }
        return isMajor ? 'text-zinc-300' : 'text-zinc-600';
    }

    function formatTickValue(val: number) {
        return val % 1 !== 0 ? val.toFixed(1) : val.toString();
    }

    function polarToCartesian(centerX: number, centerY: number, radius: number, angleInDegrees: number) {
        const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0;
        return {
            x: centerX + (radius * Math.cos(angleInRadians)),
            y: centerY + (radius * Math.sin(angleInRadians))
        };
    }

    function describeArc(x: number, y: number, radius: number, startAngle: number, endAngle: number) {
        const start = polarToCartesian(x, y, radius, startAngle);
        const end = polarToCartesian(x, y, radius, endAngle);
        const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
        return [
            "M", start.x, start.y, 
            "A", radius, radius, 0, largeArcFlag, 1, end.x, end.y
        ].join(" ");
    }
</script>

<article class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex flex-col items-center shadow-lg transition-colors duration-300 relative w-full aspect-square max-w-sm mx-auto">
    <div class="relative w-full h-full mt-4">
        <svg viewBox="0 0 100 100" class="w-full h-full overflow-visible">
            
            <path
                d={describeArc(50, 50, 40, -135, trackEndAngle)}
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
                class="text-zinc-800"
                stroke-linecap="round"
            />

            {#each Array(totalTicks + 1) as _, i}
                {@const val = min + (i * (stepSize / subdivisions))}
                
                {#if val <= max}
                    {@const isMajor = i % subdivisions === 0}
                    {@const tickAngle = -135 + ((val - min) / (scaleMax - min)) * 270}
                    {@const tickColor = getTickColorClass(val, isMajor)}
                    
                    <line
                        x1="50" y1={isMajor ? 10 : 13}
                        x2="50" y2="16"
                        stroke="currentColor"
                        stroke-width={isMajor ? 1.5 : 1}
                        transform="rotate({tickAngle} 50 50)"
                        class="transition-colors {tickColor}"
                    />

                    {#if isMajor}
                        {@const angleRad = (tickAngle - 90) * (Math.PI / 180)}
                        {@const textX = 50 + 26 * Math.cos(angleRad)}
                        {@const textY = 50 + 26 * Math.sin(angleRad)}
                        
                        <text 
                            x={textX} 
                            y={textY} 
                            text-anchor="middle" 
                            dominant-baseline="central" 
                            fill="currentColor"
                            class="text-[5.5px] font-mono transition-colors {tickColor}"
                        >
                            {formatTickValue(val)}
                        </text>
                    {/if}
                {/if}
            {/each}

            <g transform="rotate({needleAngle} 50 50)">
                <polygon points="48.5,50 51.5,50 50,18" fill="rgba(0,0,0,0.4)" transform="translate(1, 1)" />
                <polygon points="48.5,50 51.5,50 50,18" class="fill-red-500" />
                <circle cx="50" cy="50" r="4.5" class="fill-zinc-950 stroke-zinc-700" stroke-width="1.5" />
                <circle cx="50" cy="50" r="1.5" class="fill-red-500" />
            </g>
        </svg>

        <div class="absolute bottom-6 left-0 right-0 flex flex-col items-center">
            <span class="text-zinc-500 font-mono text-2xl mt-1 whitespace-pre-line text-center" aria-label="Unit: {unit}">
                {unit}
            </span>
        </div>
    </div>
</article>