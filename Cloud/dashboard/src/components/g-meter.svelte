<script lang="ts">
    import type { Snippet } from 'svelte';

    interface Props {
        x?: number; // Lateral G (Left/Right)
        y?: number; // Longitudinal G (Braking/Acceleration)
        z?: number; // Vertical G (Up/Down) - normally ~1G statically
        maxG?: number; // The highest labeled circle
        demo?: boolean;
        indicator?: Snippet; // Allows replacing the default dot with a custom SVG or element
    }

    let {
        x = 0,
        y = 0,
        z = 1.0, 
        maxG = 2,
        demo = false,
        indicator
    }: Props = $props();

    // --- Demo Animation Logic ---
    let time = $state(0);

    $effect(() => {
        if (!demo) return;
        
        const interval = setInterval(() => {
            time += 0.03; 
        }, 20);

        return () => clearInterval(interval);
    });

    // We multiply maxG by 1.25 in the demo so it intentionally spikes into the extended crosshair area!
    let displayX = $derived(demo ? Math.sin(time * 1.3) * maxG * 1.25 : x);
    let displayY = $derived(demo ? Math.cos(time * 1.1) * maxG * 1.25 : y);
    // Vertical G flutters around 1G
    let displayZ = $derived(demo ? 1 + (Math.sin(time * 0.8) * 0.5) : z);

    // Provide 25% extra space beyond the outermost maxG circle for over-the-limit spikes
    let renderLimit = $derived(maxG * 1.25);

    // Calculate magnitude to clamp against the extended renderLimit rather than maxG
    let magnitude = $derived(Math.sqrt(displayX * displayX + displayY * displayY));
    let clampedX = $derived(magnitude > renderLimit ? (displayX / magnitude) * renderLimit : displayX);
    let clampedY = $derived(magnitude > renderLimit ? (displayY / magnitude) * renderLimit : displayY);

    // Map to a 0-100 SVG coordinate system using the new extended limit
    let dotX = $derived(50 + (clampedX / renderLimit) * 50);
    let dotY = $derived(50 - (clampedY / renderLimit) * 50);
</script>

<article class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex flex-col items-center shadow-lg transition-colors duration-300 relative w-full aspect-square max-w-sm mx-auto">
    <div class="w-full flex justify-end items-start absolute top-5 left-5 right-5 z-10">        
        <div class="text-right bg-zinc-900/80 p-1 rounded">
            <div class="text-[10px] font-mono text-zinc-500">
                Lat (X): <span class="text-white">{displayX.toFixed(2)}</span>
            </div>
            <div class="text-[10px] font-mono text-zinc-500">
                Lon (Y): <span class="text-white">{displayY.toFixed(2)}</span>
            </div>
            <div class="text-[10px] font-mono text-zinc-500">
                Vert (Z): <span class="text-white">{displayZ.toFixed(2)}</span>
            </div>
        </div>
    </div>

    <div class="relative w-full h-full mt-6 p-4">
        <svg viewBox="0 0 100 100" class="w-full h-full overflow-visible">
            
            <line x1="50" y1="0" x2="50" y2="100" stroke="currentColor" stroke-width="0.5" class="text-zinc-700" />
            <line x1="0" y1="50" x2="100" y2="50" stroke="currentColor" stroke-width="0.5" class="text-zinc-700" />

            {#each Array(maxG) as _, i}
                {@const gLevel = i + 1}
                {@const radius = (gLevel / renderLimit) * 50}
                
                <circle cx="50" cy="50" r={radius} fill="none" stroke="currentColor" stroke-width="0.5" class="text-zinc-700" />
                
                <text x="50" y={50 - radius - 1} text-anchor="middle" dominant-baseline="baseline" class="text-[4px] fill-zinc-500 font-mono font-bold">
                    {gLevel}G
                </text>
            {/each}

            <g transform="translate({dotX}, {dotY})" class="transition-transform duration-100 ease-linear">
                {#if indicator}
                    {@render indicator()}
                {:else}
                    <circle cx="0" cy="0" r="4" fill="rgba(0,0,0,0.5)" transform="translate(1, 1)" />
                    <circle cx="0" cy="0" r="3.5" class="fill-red-500 stroke-zinc-950" stroke-width="1" />
                    <circle cx="-1" cy="-1" r="1" class="fill-red-400" />
                {/if}
            </g>
        </svg>
    </div>
</article>