<script lang="ts">
	import TireSet from '../../components/tires/TireSet.svelte';
	import Gauge from '../../components/gauges/analog-gauge.svelte';
	import Speedometer from '../../components/gauges/speedometer.svelte';
	import Tachometer from '../../components/gauges/tachometer.svelte';
	import GMeter from '../../components/g-meter.svelte';
	import TrackMap from '../../components/trackmap.svelte';
  import { globalSocket } from '$lib/communcation/globalSocket.svelte';
  import RollPitchCard from '../../components/rollPitch/RollPitchCard.svelte';

	let displayMode: 'analog' | 'digital' = $state('digital');
</script>

<section aria-labelledby="live-telemetry-heading" class="space-y-8 max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
    
    <header class="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 border-b border-zinc-800 pb-6">
        <div>
            <h1 id="live-telemetry-heading" class="text-3xl font-black text-white tracking-tight">Live Telemetry</h1>
            <p class="text-zinc-400 text-sm mt-1">Vehicle 04 - Currently on track</p>
        </div>
        
        <div class="flex bg-zinc-900 rounded-lg p-1 border border-zinc-800 shadow-inner">
            <button 
                class="px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-md transition-all duration-200 {displayMode === 'digital' ? 'bg-zinc-700 text-white shadow' : 'text-zinc-500 hover:text-zinc-300'}"
                onclick={() => displayMode = 'digital'}
            >
                Digital
            </button>
            <button 
                class="px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-md transition-all duration-200 {displayMode === 'analog' ? 'bg-zinc-700 text-white shadow' : 'text-zinc-500 hover:text-zinc-300'}"
                onclick={() => displayMode = 'analog'}
            >
                Analog
            </button>
        </div>
    </header>

    <div class="animate-in fade-in duration-500">
        {#if displayMode === 'digital'}
            <h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-3">Digital Cluster</h2>
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <div class="col-span-1">
                    <Speedometer value={184} unit="km/h" />
                </div>
                <div class="col-span-1 lg:col-span-2">
                    <Tachometer 
                        value={6400} 
                        max={7500} 
                        segments={25} 
						stepSize={500}
                        demo={true}
                        ranges={[
                            { min: 0, max: 5999, colorClass: 'bg-white' },
                            { min: 6000, max: 6999, colorClass: 'bg-orange-500' },
                            { min: 7000, max: 7500, colorClass: 'bg-red-500' }
                        ]}
                    />
                </div>
            </div>
        {:else}
            <h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-3">Analog Instruments</h2>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Gauge value={184} max={300} stepSize={20} intermediateTicks={1} unit="km/h" demo={true} />
                
                <Gauge 
                    value={6.4} max={7.5} precision={1} stepSize={1} intermediateTicks={4} unit="rpm{'\n'}x1000" demo={true}
                    ranges={[
                        { min: 0, max: 5.99, colorClass: 'text-white' },
                        { min: 6, max: 6.99, colorClass: 'text-orange-500' },
                        { min: 7, max: 7.5, colorClass: 'text-red-500' }
                    ]}
                />
                
                <Gauge 
                    value={4.2} max={8} stepSize={2} intermediateTicks={3} precision={1} unit="bar" demo={true}
                    ranges={[
                        { min: 0, max: 2.9, colorClass: 'text-red-500' },
                        { min: 3, max: 8, colorClass: 'text-emerald-400' }
                    ]}
                />
                
                <Gauge 
                    value={90} max={120} stepSize={20} intermediateTicks={1} unit="°C" demo={true}
                    ranges={[
                        { min: 0, max: 100, colorClass: 'text-emerald-400' },
                        { min: 101, max: 120, colorClass: 'text-red-500' }
                    ]}
                />
            </div>
        {/if}
    </div>

    <div>
        <h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-3">Dynamics & Position</h2>
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
            
            <div class="col-span-1">
                <GMeter maxG={3} x={globalSocket.current_data.Accelerometer.acceleration[1] || 0}
                                y={globalSocket.current_data.Accelerometer.acceleration[0] || 0} />
            </div>
            
            <div class="col-span-1 lg:col-span-2">
                <TrackMap demo={true} />
            </div>
            <div class="col-span-1">
                <RollPitchCard roll={globalSocket.current_data.Accelerometer.roll || 0} pitch={globalSocket.current_data.Accelerometer.pitch || 0}></RollPitchCard>
            </div>
        </div>
    </div>

    <div>
        <h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-3">Tyre Status</h2>
        <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-4 shadow-lg">
            <TireSet layerCount={3} />
        </div>
    </div>

</section>