<script lang="ts">
    import TireLayer from "./TireLayer.svelte";
    import TireData from "./TireData.svelte";

    interface Props {
        statsPosition?: 'left' | 'right' | 'top' | 'bottom';
        layerCount?: number; 
    }
    let { statsPosition = 'left', layerCount = 3 }: Props = $props();

    let baseTemp: number = $state<number>(0.0);
    let time = 0;

    let speed = $derived(Math.max(0, Math.sin(time / 1.5) * 150 + 100));
    let pressure = $derived(22 + (baseTemp / 20)); 

    let validLayerCount = $derived(Math.max(1, Math.min(3, layerCount)));

    let temperatures = $derived.by(() => {
        let temps = [baseTemp];
        if (validLayerCount > 1) temps.push(baseTemp - 15);
        if (validLayerCount > 2) temps.push(baseTemp - 30);
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

    $effect(() => {
        const interval = setInterval(() => {
            time += 0.02;
            baseTemp = 100 + Math.sin(time) * 100; 
        }, 50);

        return () => clearInterval(interval);
    });
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