<script lang="ts">
    interface Props {
        title?: string;
        xmlUrl?: string; 
        progress?: number; 
        demo?: boolean;
    }

    let {
        title = "Track Map",
        xmlUrl = "/track-metadata.xml", // Back to your working static path!
        progress = 0,
        demo = false
    }: Props = $props();

    interface Circuit {
        id: string;
        name: string;
        city: string;
        country: string;
        lengthKm: string;
        corners: string;
        firstGp: string;
        racesHeld: string;
        lapRecord: { time: string; driver: string; year: string; };
        svgFile: string; 
    }

    let circuits = $state<Circuit[]>([]);
    let selectedId = $state<string>('');
    let activeCircuit = $derived(circuits.find(c => c.id === selectedId));

    // Dynamic SVG State
    let activeViewBox = $state('0 0 800 800');
    let activePathString = $state('');

    let pathElement: SVGPathElement | undefined = $state();
    let dotX = $state(0);
    let dotY = $state(0);
    let displayProgress = $state(progress);

    // --- 1. Fetch XML (Restored to your working method) ---
    $effect(() => {
        fetch(xmlUrl)
            .then(res => res.text())
            .then(xmlString => {
                const parser = new DOMParser();
                const xmlDoc = parser.parseFromString(xmlString, "text/xml");
                const circuitNodes = xmlDoc.querySelectorAll('circuit');
                
                circuits = Array.from(circuitNodes).map(node => ({
                    id: node.getAttribute('id') || '',
                    name: node.querySelector('name')?.textContent || 'Unknown Track',
                    city: node.querySelector('city')?.textContent || '',
                    country: node.querySelector('country')?.textContent || '',
                    lengthKm: node.querySelector('length_km')?.textContent || '0',
                    corners: node.querySelector('corners')?.textContent || '0',
                    firstGp: node.querySelector('first_gp')?.textContent || '',
                    racesHeld: node.querySelector('races_held')?.textContent || '0',
                    lapRecord: {
                        time: node.querySelector('lap_record time')?.textContent || '--:--',
                        driver: node.querySelector('lap_record driver')?.textContent || 'N/A',
                        year: node.querySelector('lap_record year')?.textContent || ''
                    },
                    svgFile: node.querySelector('svg_file')?.textContent?.trim() || ''
                }));

                if (circuits.length > 0 && !selectedId) {
                    selectedId = circuits[0].id;
                }
            })
            .catch(err => console.error("Error loading circuits XML:", err));
    });

    // --- 2. Auto-Extract SVG Data (Runs when track changes) ---
    $effect(() => {
        if (activeCircuit?.svgFile) {
            // Reset while loading
            activePathString = ''; 
            
            fetch(activeCircuit.svgFile)
                .then(res => res.text())
                .then(svgText => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(svgText, "image/svg+xml");
                    
                    const svgNode = doc.querySelector('svg');
                    // Find the first path in the file
                    const pathNode = doc.querySelector('path'); 
                    
                    if (svgNode && pathNode) {
                        activeViewBox = svgNode.getAttribute('viewBox') || '0 0 800 800';
                        activePathString = pathNode.getAttribute('d') || '';
                    }
                })
                .catch(err => console.error("Failed to load SVG file:", err));
        }
    });

    // --- 3. Demo Animation Logic ---
    $effect(() => {
        if (!demo) {
            displayProgress = progress;
            return;
        }
        const interval = setInterval(() => {
            displayProgress = (displayProgress + 0.0015) % 1; 
        }, 20);
        return () => clearInterval(interval);
    });

    // --- 4. Path Math Logic ---
    $effect(() => {
        if (pathElement && activePathString) {
            try {
                const totalLength = pathElement.getTotalLength();
                const currentLength = totalLength * displayProgress;
                const point = pathElement.getPointAtLength(currentLength);
                dotX = point.x;
                dotY = point.y;
            } catch (e) {
                dotX = 0; dotY = 0;
            }
        }
    });

    function getCountryCode(country: string) {
        const map: Record<string, string> = {
            'Australia': 'au', 'China': 'cn', 'Japan': 'jp', 'Bahrain': 'bh',
            'Saudi Arabia': 'sa', 'USA': 'us', 'Canada': 'ca', 'Monaco': 'mc',
            'Spain': 'es', 'Austria': 'at', 'Great Britain': 'gb', 'Belgium': 'be',
            'Hungary': 'hu', 'Netherlands': 'nl', 'Italy': 'it', 'Azerbaijan': 'az',
            'Singapore': 'sg', 'Mexico': 'mx', 'Brazil': 'br', 'Qatar': 'qa', 'UAE': 'ae'
        };
        return map[country] || 'un';
    }
</script>

<article class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex flex-col shadow-lg w-full h-full min-h-[400px]">
    {#if activeCircuit}
        <div class="flex justify-between items-start mb-4">
            <div class="flex-1">
                <h3 class="text-zinc-400 text-xs font-bold uppercase tracking-widest mb-1">{title}</h3>
                <div class="flex items-center gap-2">
                    <img 
                        src="https://flagcdn.com/w20/{getCountryCode(activeCircuit.country)}.png" 
                        alt="{activeCircuit.country} flag"
                        class="h-3 w-auto rounded-sm opacity-90"
                    />
                    <select 
                        bind:value={selectedId} 
                        class="bg-zinc-800 border border-zinc-700 text-white font-medium text-sm rounded px-2 py-1 outline-none focus:border-red-500 transition-colors cursor-pointer"
                    >
                        {#each circuits as circuit}
                            <option value={circuit.id}>{circuit.name}</option>
                        {/each}
                    </select>
                </div>
            </div>
            
            <div class="text-right shrink-0">
                <span class="text-[10px] font-mono text-zinc-500 block uppercase">Lap Progress</span>
                <span class="text-emerald-400 font-mono font-bold text-lg leading-none tracking-tighter">
                    {(displayProgress * 100).toFixed(1)}%
                </span>
            </div>
        </div>

        <div class="relative w-full flex items-center justify-center flex-1 p-6 bg-zinc-950/50 rounded-lg border border-zinc-800/50 mb-4 overflow-hidden">
            {#if activePathString}
                <svg viewBox={activeViewBox} class="w-full h-full max-h-62.5 overflow-visible drop-shadow-lg">
                    <path
                        bind:this={pathElement}
                        d={activePathString}
                        fill="none"
                        stroke="currentColor"
                        stroke-width="3"
                        class="text-zinc-600"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    />
                    {#if pathElement && (dotX !== 0 || dotY !== 0)}
                        <g transform="translate({dotX}, {dotY})" class="transition-transform duration-75 ease-linear">
                            <circle cx="0" cy="0" r="6" class="fill-emerald-400/30 animate-ping" />
                            <circle cx="0" cy="0" r="4.5" fill="rgba(0,0,0,0.6)" transform="translate(1, 1)" />
                            <circle cx="0" cy="0" r="3.5" class="fill-emerald-400 stroke-zinc-900" stroke-width="1.5" />
                        </g>
                    {/if}
                </svg>
            {:else}
                <div class="text-zinc-600 text-sm font-mono animate-pulse">
                    Loading track map...
                </div>
            {/if}
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-auto border-t border-zinc-800/50 pt-4">
            </div>
    {/if}
</article>