<script lang="ts">
    import TireLayer from "./TireLayer.svelte";
    import TireData from "./TireData.svelte";

    interface Props {
        statsPosition?: 'left' | 'right' | 'top' | 'bottom';
        layerCount?: number;
        surfaceTemp?: number;
        pressure?: number;
        speed?: number;
        demo?: boolean;
    }
    let {
        statsPosition = 'left',
        layerCount = 3,
        surfaceTemp = 0,
        pressure = 0,
        speed = 0,
        demo = false
    }: Props = $props();

    let demoTime = $state(0);
    let demoBaseTemp = $state(0);

    $effect(() => {
        if (!demo) return; // Only run the loop if demo is true!

        const interval = setInterval(() => {
            demoTime += 0.02;
            demoBaseTemp = 100 + Math.sin(demoTime) * 100;
        }, 50);

        return () => clearInterval(interval);
    });

    // --- THE SWITCHER LOGIC ---
    // These derived values automatically pick the right data source
    let activeSpeed = $derived(demo ? Math.max(0, Math.sin(demoTime / 1.5) * 150 + 100) : speed);
    let activeSurfaceTemp = $derived(demo ? demoBaseTemp : surfaceTemp);
    let activePressure = $derived(demo ? 22 + (demoBaseTemp / 20) : pressure);

    // Derive internal temp based on whichever pressure is currently active
    let internalTemp = $derived(activePressure * 1.6);

    let validLayerCount = $derived(Math.max(1, Math.min(3, layerCount)));

    let temperatures = $derived.by(() => {
        let temps = [activeSurfaceTemp];
        if (validLayerCount > 1) temps.push(internalTemp);
        if (validLayerCount > 2) temps.push(internalTemp - 5);
        return temps;
    });

    function getTempColor(temp: number): string {
        const t = Math.max(0, Math.min(200, temp));
        let hue: number;

        if (t <= 90) {
            const progress = t / 90;
            hue = 240 - (progress * 120); 
        } else if (t <= 100) {
            hue = 120; 
        } else {
            const progress = (t - 100) / 100;
            hue = 120 - (progress * 120);
        }

        return `hsl(${hue}, 85%, 50%)`;
    }
</script>

<div class="m-2 flex items-center justify-center gap-4
    {statsPosition === 'left' ? 'flex-row-reverse' : ''}
    {statsPosition === 'right' ? 'flex-row' : ''}
    {statsPosition === 'top' ? 'flex-col-reverse' : ''}
    {statsPosition === 'bottom' ? 'flex-col' : ''}
">
    
    <div class="w-20">
        {#if temperatures.length === 1}
            <TireLayer colour={getTempColor(temperatures[0])} outer={true} radius={24} />
            
        {:else if temperatures.length === 2}
            <TireLayer colour={getTempColor(temperatures[0])} outer={true} radius={24}>
                <TireLayer colour={getTempColor(temperatures[1])} />
            </TireLayer>
            
        {:else if temperatures.length === 3}
            <TireLayer colour={getTempColor(temperatures[0])} outer={true} radius={24}>
                <TireLayer colour={getTempColor(temperatures[1])}>
                    <TireLayer colour={getTempColor(temperatures[2])} />
                </TireLayer>
            </TireLayer>
        {/if}
    </div>

    <TireData {speed} {pressure} {temperatures} {getTempColor} />

</div>