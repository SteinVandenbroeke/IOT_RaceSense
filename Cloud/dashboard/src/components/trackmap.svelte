<script lang="ts">
    interface Props {
        title?: string;
        xmlUrl?: string; 
        progress?: number; 
        demo?: boolean;
    }

    let {
        title = "Track Map",
        xmlUrl = "/track-metadata.xml",
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

    // --- State ---
    let circuits = $state<Circuit[]>([]);
    let selectedId = $state<string>('');
    let activeCircuit = $derived(circuits.find(c => c.id === selectedId));

    // UI State for Search
    let isExpanded = $state(false);
    let searchQuery = $state('');
    let activeIndex = $state(-1);
    let inputElement: HTMLInputElement | undefined = $state();
    let listItems: HTMLLIElement[] = $state([]);

    // Dynamic SVG State
    let activeViewBox = $state('0 0 800 800');
    let activePathString = $state('');
    let pathElement: SVGPathElement | undefined = $state();
    let dotX = $state(0);
    let dotY = $state(0);
    let displayProgress = $state(progress);

    let filteredCircuits = $derived(
        searchQuery.trim() === ''
            ? circuits
            : circuits
                .filter(c =>
                    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    c.country.toLowerCase().includes(searchQuery.toLowerCase())
                )
                .sort((a, b) => {
                    const query = searchQuery.toLowerCase();
                    const aNameMatch = a.name.toLowerCase().includes(query);
                    const bNameMatch = b.name.toLowerCase().includes(query);

                    // Priority: If 'a' matches by name and 'b' doesn't, 'a' comes first
                    if (aNameMatch && !bNameMatch) return -1;
                    if (!aNameMatch && bNameMatch) return 1;
                    return 0;
                })
    );
    // --- Logic ---
    function selectCircuit(id: string) {
        selectedId = id;
        closeSearch();
    }

    function closeSearch() {
        isExpanded = false;
        searchQuery = '';
        activeIndex = -1;
        inputElement?.blur();
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            activeIndex = activeIndex < filteredCircuits.length - 1 ? activeIndex + 1 : activeIndex;
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            activeIndex = activeIndex > 0 ? activeIndex - 1 : 0;
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (activeIndex >= 0 && filteredCircuits[activeIndex]) {
                selectCircuit(filteredCircuits[activeIndex].id);
            }
        } else if (e.key === 'Escape') {
            closeSearch();
        }
    }

    function clickOutside(node: HTMLElement) {
        const handleClick = (event: MouseEvent) => {
            if (!node.contains(event.target as Node)) closeSearch();
        };
        document.addEventListener('click', handleClick, true);
        return { destroy() { document.removeEventListener('click', handleClick, true); } };
    }

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

    // --- Effects ---
    $effect(() => {
        if (activeIndex !== -1 && listItems[activeIndex]) {
            listItems[activeIndex].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
    });

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
                if (circuits.length > 0 && !selectedId) selectedId = circuits[0].id;
            });
    });
    let calculationPathString = $state('');
    function cleanAndExtractTrack(svgText: string) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(svgText, "image/svg+xml");
        const pathData = doc.querySelector('path')?.getAttribute('d') || '';

        // 1. Split the compound path into individual sub-paths
        // Your SVG has 3 parts: Outer Wall, Inner Wall, and Arrow.
        const subPaths = pathData.split(/(?=m|M)/).filter(p => p.trim().length > 0);

        // 2. Identify the two longest sub-paths (the walls)
        const sortedPaths = subPaths.sort((a, b) => b.length - a.length);
        const wallA = sortedPaths[0]; // Outer
        const wallB = sortedPaths[1]; // Inner

        // 3. To get a center-line, we can simply use ONE of these walls 
        // and ignore the "return trip" and the arrow.
        // This stops the "switching sides" and "reversing" behavior.
        return {
            visualOutline: wallA + wallB, // The full track look
            drivingLine: wallA,          // The path the dot follows
            viewBox: doc.querySelector('svg')?.getAttribute('viewBox') || '0 0 800 800'
    };
}

    // 1. Fetch SVG and find the LONGEST path (usually the track itself)
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
                        
                        // VISUAL: Keep the whole ribbon
                        activePathString = fullD; 

                        // MATH: Split the string at 'M' and take only the first loop (the outer wall)
                        // This ignores the arrow and the "return" trip
                        const subPaths = fullD.split(/(?=[mM])/);
                        calculationPathString = subPaths[0] || fullD; 
                    }
                });
        }
    });

    // 2. Optimized Path Math to prevent "reversing"
    $effect(() => {
        if (pathElement && calculationPathString) {
            try {
                const totalLength = pathElement.getTotalLength();
                const currentLength = totalLength * (displayProgress % 1);
                
                // 1. Get the current point on the outer wall
                const point = pathElement.getPointAtLength(currentLength);
                
                // 2. Look slightly ahead to figure out which way the track is going
                const lookAheadLength = (currentLength + 1) % totalLength;
                const nextPoint = pathElement.getPointAtLength(lookAheadLength);
                
                // 3. Calculate the tangent vector (direction)
                const dx = nextPoint.x - point.x;
                const dy = nextPoint.y - point.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                // 4. Calculate the Normal vector (90 degrees to the tangent)
                // Note: If the dot shifts OUTSIDE the track, flip these to (-dy/distance) and (dx/distance)
                const nx = dy / distance;  
                const ny = -dx / distance; 

                // 5. Apply the offset (e.g., 6 SVG units inward)
                const offsetAmount = 6; 
                
                dotX = point.x + (nx * offsetAmount);
                dotY = point.y + (ny * offsetAmount);
                
            } catch (e) {
                dotX = 0; dotY = 0;
            }
        }
    });

    $effect(() => {
        if (!demo) { displayProgress = progress; return; }
        const interval = setInterval(() => { displayProgress = (displayProgress + 0.0015) % 1; }, 20);
        return () => clearInterval(interval);
    });

</script>

<article class="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col shadow-lg w-full h-full min-h-[300px]">
    {#if activeCircuit}
        <div class="flex justify-between items-start mb-4">
            <div class="flex-1">
                <div class="flex items-center gap-2 mb-1">
                    <img 
                        src="https://flagcdn.com/w20/{getCountryCode(activeCircuit.country)}.png" 
                        alt={activeCircuit.country}
                        class="h-3 w-auto rounded-sm opacity-80"
                    />
                    <span class="text-zinc-500 text-[10px] font-bold uppercase tracking-widest">
                        {activeCircuit.country} <span class="mx-1 text-zinc-700">|</span> {activeCircuit.city}
                    </span>
                </div>
                
                <div class="flex items-center gap-3">
                    <h3 class="text-white text-xl font-bold tracking-tight leading-none">
                        {activeCircuit.name}
                    </h3>

                    <div class="relative" use:clickOutside>
                        <div class="flex items-center bg-zinc-800/50 rounded-full transition-all duration-300 {isExpanded ? 'w-48 px-2 bg-zinc-800 border border-zinc-700' : 'w-8 h-8 justify-center hover:bg-zinc-800'}">
                            <button 
                                onclick={() => { isExpanded = !isExpanded; if(isExpanded) setTimeout(() => inputElement?.focus(), 10); }}
                                class="text-zinc-400 hover:text-emerald-400 transition-colors shrink-0"
                            >
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                            </button>
                            
                            {#if isExpanded}
                                <input
                                    bind:this={inputElement}
                                    type="text"
                                    bind:value={searchQuery}
                                    onkeydown={handleKeydown}
                                    placeholder="Find track..."
                                    class="bg-transparent border-none text-white text-xs pl-2 w-full placeholder:text-zinc-500 focus:ring-0 focus:outline-none"
                                />
                            {/if}
                        </div>

                        {#if isExpanded && searchQuery.length > 0}
                            <ul class="absolute z-50 left-0 mt-2 w-64 bg-zinc-800 border border-zinc-700 rounded-lg shadow-2xl max-h-60 overflow-y-auto custom-scrollbar">
                                {#each filteredCircuits as circuit, i (circuit.id)}
                                    <li
                                        bind:this={listItems[i]}
                                        onclick={() => selectCircuit(circuit.id)}
                                        class="px-4 py-2.5 cursor-pointer border-b border-zinc-700/50 last:border-0 transition-colors 
                                        {activeIndex === i ? 'bg-zinc-700' : 'hover:bg-zinc-700'}"
                                    >
                                        <div class="text-xs font-bold {selectedId === circuit.id ? 'text-emerald-400' : 'text-zinc-200'}">
                                            {circuit.name}
                                        </div>
                                    </li>
                                {/each}
                            </ul>
                        {/if}
                    </div>
                </div>
            </div>
            
            <div class="text-right shrink-0">
                <span class="text-[9px] font-mono text-zinc-500 block uppercase">Lap Progress</span>
                <span class="text-emerald-400 font-mono font-bold text-base leading-none tracking-tighter">
                    {(displayProgress * 100).toFixed(1)}%
                </span>
            </div>
        </div>
    <div class="relative w-full flex items-center justify-center flex-1 py-2 overflow-hidden">
        {#if activePathString}
            <svg viewBox={activeViewBox} class="w-full h-full max-h-[250px] overflow-visible drop-shadow-lg">
                
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

        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-auto border-t border-zinc-800/50 pt-3">
            <div>
                <span class="text-[9px] font-bold text-zinc-600 uppercase block tracking-wider">Length</span>
                <span class="text-zinc-300 font-mono text-xs">{activeCircuit.lengthKm} km</span>
            </div>
            <div>
                <span class="text-[9px] font-bold text-zinc-600 uppercase block tracking-wider">Turns</span>
                <span class="text-zinc-300 font-mono text-xs">{activeCircuit.corners}</span>
            </div>
            <div class="col-span-2 md:col-span-2">
                <span class="text-[9px] font-bold text-zinc-600 uppercase block tracking-wider flex items-center gap-1">
                    Lap Record <span class="text-zinc-700">({activeCircuit.lapRecord.year})</span>
                </span>
                <div class="flex items-baseline justify-between">
                    <span class="text-emerald-400 font-mono text-xs font-bold">{activeCircuit.lapRecord.time}</span>
                    <span class="text-zinc-500 font-mono text-[10px] truncate ml-2">{activeCircuit.lapRecord.driver}</span>
                </div>
            </div>
        </div>
    {/if}
</article>