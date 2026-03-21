<script lang="ts">
    interface Props {
        speed: number;
        pressure: number;
        temperatures: number[];
        getTempColor: (temp: number) => string;
    }

    let { speed, pressure, temperatures, getTempColor }: Props = $props();

    let isCollapsed = $state<boolean>(true);

    // Moved the labeling helper directly into the card
    function getLayerLabel(index: number, total: number) {
        if (total === 1) return 'Surface';
        if (total === 2) return index === 0 ? 'Surface' : 'Core';
        if (total === 3) {
            if (index === 0) return 'Surface';
            if (index === 1) return 'Middle';
            return 'Core';
        }
        return '';
    }
</script>

<div class="flex flex-col gap-1 font-mono text-sm bg-gray-900 text-white p-3 rounded-md shadow-lg min-w-[150px]">
    
    <div class="flex justify-between">
        <span class="text-gray-400">Wheel Speed:</span> 
        <span>{Math.round(speed)} km/h</span>
    </div>
    
    <div class="flex justify-between border-b border-gray-700 pb-2 mb-1">
        <span class="text-gray-400">Pressure:</span> 
        <span>{pressure.toFixed(1)} psi</span>
    </div>

    {#if temperatures.length === 1}
        
        <div class="flex justify-between pl-2">
            <span>{getLayerLabel(0, 1)}: </span> 
            <span style="color: {getTempColor(temperatures[0])}">{Math.round(temperatures[0])}°C</span>
        </div>

    {:else}

        <button 
            class="flex justify-between items-center w-full text-left text-gray-400 hover:text-white cursor-pointer transition-colors pt-1 pb-1"
            onclick={() => isCollapsed = !isCollapsed}
        >
            <span>Temperatures</span>
            <span class="text-xs">{isCollapsed ? '▼' : '▲'}</span>
        </button>

        {#if isCollapsed}
            <div class="flex justify-between pl-2">
                <span>{getLayerLabel(0, temperatures.length)}: </span> 
                <span style="color: {getTempColor(temperatures[0])}">{Math.round(temperatures[0])}°C</span>
            </div>
        {:else}
            {#each temperatures as temp, i}
                <div class="flex justify-between pl-2">
                    <span>{getLayerLabel(i, temperatures.length)}:</span> 
                    <span style="color: {getTempColor(temp)}">{Math.round(temp)}°C</span>
                </div>
            {/each}
        {/if}

    {/if}
</div>