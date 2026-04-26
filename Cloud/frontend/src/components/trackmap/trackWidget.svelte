<script lang="ts">
    import type { Circuit } from './circuit';
    import TrackSelector from './trackSelector.svelte';
    import TrackMap from './trackMap.svelte';
    import TrackInfo from './trackInfo.svelte';

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

    let circuits = $state<Circuit[]>([]);
    let selectedId = $state<string>('');
    let activeCircuit = $derived(circuits.find(c => c.id === selectedId));
    let displayProgress = $state(progress);

    // Fetch Initial XML Data
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

    // Handle Demo Animation Interval
    $effect(() => {
        if (!demo) { displayProgress = progress; return; }
        const interval = setInterval(() => { displayProgress = (displayProgress + 0.0015) % 1; }, 20);
        return () => clearInterval(interval);
    });
</script>

<article class="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col shadow-lg w-full h-full min-h-[300px]">
    {#if activeCircuit}
        <TrackSelector 
            {circuits} 
            bind:selectedId 
            {activeCircuit} 
            {displayProgress} 
        />
        
        <TrackMap 
            {activeCircuit} 
            {displayProgress} 
        />
        
        <TrackInfo 
            {activeCircuit} 
        />
    {/if}
</article>