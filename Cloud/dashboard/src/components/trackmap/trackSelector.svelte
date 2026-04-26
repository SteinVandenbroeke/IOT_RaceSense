<script lang="ts">
    import type { Circuit } from './types';

    let {
        circuits,
        selectedId = $bindable(),
        activeCircuit,
        displayProgress
    }: {
        circuits: Circuit[];
        selectedId: string;
        activeCircuit: Circuit;
        displayProgress: number;
    } = $props();

    // Search State
    let isExpanded = $state(false);
    let searchQuery = $state('');
    let activeIndex = $state(-1);
    let inputElement: HTMLInputElement | undefined = $state();
    let listItems: HTMLLIElement[] = $state([]);

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
</script>

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
        
        <div class="flex items-center relative h-8 w-full max-w-70 sm:max-w-[320px]" use:clickOutside>
            <h3 class="text-white text-xl font-bold tracking-tight leading-none whitespace-nowrap truncate transition-opacity duration-300 {isExpanded ? 'opacity-0' : 'opacity-100'}">
                {activeCircuit.name}
            </h3>

            <div 
                role="button"
                tabindex="0"
                class="absolute right-0 flex items-center rounded-full overflow-hidden transition-all duration-700 ease-out h-8 z-10 {isExpanded ? 'w-full bg-zinc-800 ring-1 ring-zinc-700 shadow-xl' : 'w-8 bg-zinc-800/50 hover:bg-zinc-700 cursor-pointer'}"
                onclick={() => { if (!isExpanded) { isExpanded = true; setTimeout(() => inputElement?.focus(), 50); } }}
                onkeydown={(e) => { 
                    if (!isExpanded && (e.key === 'Enter' || e.key === ' ')) { 
                        e.preventDefault(); 
                        isExpanded = true; 
                        setTimeout(() => inputElement?.focus(), 50); 
                    } 
                }}
            >
                <button 
                    aria-label="Expand search"
                    class="flex items-center justify-center w-8 h-8 shrink-0 text-zinc-400 focus:outline-none transition-colors {isExpanded ? 'cursor-default' : 'hover:text-emerald-400'}"
                >                    
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
                    class="flex-1 min-w-0 bg-transparent border-none text-white text-xs p-0 focus:ring-0 focus:outline-none transition-opacity duration-300 delay-100 {isExpanded ? 'opacity-100' : 'opacity-0'}"
                />

                {#if isExpanded}
                    <button 
                        aria-label="Clear search or close"
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

            {#if isExpanded && searchQuery.length > 0}
                <ul class="absolute z-50 left-0 top-full mt-2 w-full bg-zinc-800 border border-zinc-700 rounded-lg shadow-2xl max-h-60 overflow-y-auto custom-scrollbar">
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