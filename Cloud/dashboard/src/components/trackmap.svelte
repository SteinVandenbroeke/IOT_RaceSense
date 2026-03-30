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
        svgReverse: boolean;
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

    $effect(() => {
        if (activeIndex !== -1 && listItems[activeIndex]) {
            listItems[activeIndex].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
    });

    // --- XML Fetcher ---
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
                    svgFile: node.querySelector('svg_file')?.textContent?.trim() || '',
                    svgReverse: node.querySelector('svg_reverse')?.textContent === 'true'
                }));
                if (circuits.length > 0 && !selectedId) selectedId = circuits[0].id;
            });
    });

    let calculationPathString = $state('');

    // --- SVG Path Fetcher ---
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

    // --- Path Math ---
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

    $effect(() => {
        if (!demo) { displayProgress = progress; return; }
        const interval = setInterval(() => { displayProgress = (displayProgress + 0.0015) % 1; }, 20);
        return () => clearInterval(interval);
    });
</script>

<article class="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col shadow-lg w-full h-full min-h-[300px]">
    {#if activeCircuit}
        <div class="flex justify-between items-start mb-4">
            
            <div class="flex-1 min-w-0 pr-4">
                <div class="flex items-center gap-2 mb-1">
                    <img 
                        src="https://flagcdn.com/w20/{getCountryCode(activeCircuit.country)}.png" 
                        alt={activeCircuit.country}
                        class="h-3 w-auto rounded-sm opacity-80"
                    />
                    <span class="text-zinc-500 text-[10px] font-bold uppercase tracking-widest truncate">
                        {activeCircuit.country} <span class="mx-1 text-zinc-700">|</span> {activeCircuit.city}
                    </span>
                </div>
                
            <div class="flex items-center h-8 relative w-full" use:clickOutside>
                
                <div class="relative inline-flex items-center max-w-[calc(100%-40px)] pr-9">
                    
                    <h3 class="text-white text-xl font-bold tracking-tight leading-none whitespace-nowrap truncate transition-opacity duration-500 {isExpanded ? 'opacity-0' : 'opacity-100'}">
                        {activeCircuit.name}
                    </h3>

                    <div 
                        class="absolute right-0 flex items-center rounded-full overflow-hidden transition-all duration-500 ease-in-out h-8 z-10
                        {isExpanded 
                            ? 'w-[280px] sm:w-[320px] bg-zinc-800 ring-1 ring-zinc-700 shadow-xl' 
                            : 'w-8 bg-zinc-800/50 hover:bg-zinc-700 cursor-pointer'}"
                        onclick={() => { if (!isExpanded) { isExpanded = true; setTimeout(() => inputElement?.focus(), 50); } }}
                    >
                        
                        <button class="flex items-center justify-center w-8 h-8 shrink-0 text-zinc-400 focus:outline-none transition-colors {isExpanded ? 'cursor-default' : 'hover:text-emerald-400'}">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                        </button>
                        
                        <input
                            bind:this={inputElement}
                            type="text"
                            bind:value={searchQuery}
                            onkeydown={handleKeydown}
                            placeholder="Find track..."
                            class="flex-1 min-w-0 bg-transparent border-none text-white text-xs p-0 focus:ring-0 focus:outline-none transition-opacity duration-300 {isExpanded ? 'opacity-100' : 'opacity-0'}"
                        />

                        {#if isExpanded}
                            <button 
                                onclick={(e) => { 
                                    e.stopPropagation();
                                    if (searchQuery.length > 0) {
                                        searchQuery = '';
                                        inputElement?.focus();
                                    } else {
                                        closeSearch();
                                    }
                                }}
                                class="flex items-center justify-center w-8 h-8 shrink-0 text-zinc-500 hover:text-white"
                            >
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        {/if}
                    </div>
                </div>

                {#if isExpanded && searchQuery.length > 0}
                    <ul class="absolute z-50 left-0 top-full mt-2 w-full max-w-[280px] sm:max-w-[320px] bg-zinc-800 border border-zinc-700 rounded-lg shadow-2xl max-h-60 overflow-y-auto custom-scrollbar">
                        {#each filteredCircuits as circuit, i (circuit.id)}
                            <li
                                bind:this={listItems[i]}
                                onclick={() => selectCircuit(circuit.id)}
                                class="px-4 py-2.5 cursor-pointer border-b border-zinc-700/50 last:border-0 transition-colors {activeIndex === i ? 'bg-zinc-700' : 'hover:bg-zinc-700'}"
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
    {/if}
</article>