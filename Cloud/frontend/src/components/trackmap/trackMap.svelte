<script lang="ts">
    import type { Circuit } from './circuit';

    let {
        activeCircuit,
        displayProgress
    }: {
        activeCircuit: Circuit;
        displayProgress: number;
    } = $props();

    let activeViewBox = $state('0 0 800 800');
    let activePathString = $state('');
    let calculationPathString = $state('');
    let pathElement: SVGPathElement | undefined = $state();
    
    let dotX = $state(0);
    let dotY = $state(0);

    // Fetch SVG
    $effect(() => {
        if (activeCircuit?.svgFile) {
            fetch(activeCircuit.svgFile)
                .then(res => res.text())
                .then(svgText => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(svgText, "image/svg+xml");
                    const svgNode = doc.querySelector('svg');
                    const pathNode = doc.querySelector('path'); 
                    
                    if (svgNode && pathNode) {
                        activeViewBox = svgNode.getAttribute('viewBox') || '0 0 800 800';
                        const fullD = pathNode.getAttribute('d') || '';
                        activePathString = fullD; 
                        const subPaths = fullD.split(/(?=[mM])/);
                        calculationPathString = subPaths[0] || fullD; 
                    }
                });
        }
    });

    // Path Math
    $effect(() => {
        if (pathElement && calculationPathString && activeCircuit) {
            try {
                const totalLength = pathElement.getTotalLength();
                let currentProgress = displayProgress % 1;
                
                if (activeCircuit.svgReverse) {
                    currentProgress = 1 - currentProgress; 
                }
                
                const currentLength = totalLength * currentProgress;
                const point = pathElement.getPointAtLength(currentLength);
                
                let nextProgress = (displayProgress + 0.005) % 1;
                if (activeCircuit.svgReverse) {
                    nextProgress = 1 - nextProgress;
                }
                const lookAheadLength = totalLength * nextProgress;
                const nextPoint = pathElement.getPointAtLength(lookAheadLength);
                
                const dx = nextPoint.x - point.x;
                const dy = nextPoint.y - point.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                let nx = dy / distance;
                let ny = -dx / distance; 
                
                if (activeCircuit.svgReverse) {
                    nx = -dy / distance;
                    ny = dx / distance;
                }

                const offsetAmount = 6;
                dotX = point.x + (nx * offsetAmount);
                dotY = point.y + (ny * offsetAmount);
            } catch (e) {
                dotX = 0;
                dotY = 0;
            }
        }
    });
</script>

<div class="relative w-full flex items-center justify-center flex-1 py-2 overflow-hidden">
    {#if activePathString}
        <svg viewBox={activeViewBox} class="w-full h-full max-h-62.5 overflow-visible drop-shadow-lg">
            <path
                d={activePathString}
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                class="text-zinc-500"
                stroke-linecap="round"
                stroke-linejoin="round"
            />
            <path
                bind:this={pathElement}
                d={calculationPathString}
                fill="none"
                stroke="transparent" 
                pointer-events="none"
            />
            {#if pathElement && calculationPathString && (dotX !== 0 || dotY !== 0)}
                <g transform="translate({dotX}, {dotY})" class="transition-transform duration-75 ease-linear">
                    <circle cx="0" cy="0" r="10" class="fill-emerald-400/40 animate-ping" />
                    <circle cx="0" cy="0" r="6" fill="rgba(0,0,0,0.8)" />
                    <circle cx="0" cy="0" r="4" class="fill-emerald-400" />
                </g>
            {/if}
        </svg>
    {/if}
</div>