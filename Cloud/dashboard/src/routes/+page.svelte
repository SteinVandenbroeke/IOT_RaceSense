<script lang="ts">
	import SensorCard from '../components/SensorCard.svelte';
	import TyreWidget from '../components/Tires.svelte';
	import TireSet from '../components/tires/TireSet.svelte';
	import Gauge from '../components/gauges/analog-gauge.svelte';
	import Speedometer from '../components/gauges/speedometer.svelte';
	import Tachometer from '../components/gauges/tachometer.svelte';
	import GMeter from '../components/g-meter.svelte';
	import Trackmap from '../components/trackmap.svelte';
</script>

<section aria-labelledby="live-telemetry-heading" class="space-y-8 max-w-7xl mx-auto">
	<header>s
		<h1 id="live-telemetry-heading" class="text-2xl font-black text-white">Live Telemetry</h1>
		<p class="text-zinc-400 text-sm">Vehicle 04 - Currently on track</p>
	</header>

	<div>
		<h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-3">General Metrics</h2>
		<ul class="grid grid-cols-1 md:grid-cols-3 gap-4">
			<li><SensorCard title="Current Speed" value={184} unit="km/h" status="normal" /></li>
			<li><SensorCard title="RPM" value="6,400" unit="rev/min" status="warning" /></li>
			<li><SensorCard title="Brake Bias" value={54} unit="%" status="normal" /></li>
		</ul>
	</div>

	<div>
		<h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-3">Tyre Status</h2>
		<ul class="grid grid-cols-1 sm:grid-cols-2 gap-4">
			<li>
				<TyreWidget title="Front Left (FL)" temp={112} tempStat="hot" pressure={1.9} presStat="high" />
			</li>
			<li>
				<TyreWidget title="Front Right (FR)" temp={103} tempStat="normal" pressure={1.7} presStat="normal" />
			</li>
			<li>
				<TyreWidget title="Rear Left (RL)" temp={98} tempStat="normal" pressure={1.6} presStat="normal" />
			</li>
			<li>
				<TyreWidget title="Rear Right (RR)" temp={97} tempStat="normal" pressure={0.8} presStat="flat" />
			</li>
		</ul>
		<TireSet/>
	</div>

	<div>
		<h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-3">Live Dials</h2>
		<ul class="grid grid-cols-1 md:grid-cols-3">
			
			<li>
				<Gauge 
					value={184} 
					max={300} 
					unit="km/h" 
					stepSize={30} 
					intermediateTicks={2}
					demo={true}
				/>
			</li>

			<li>
				<Gauge 
					value={6.4} 
					max={7.5}
					precision={1} 
					stepSize={1}
					intermediateTicks={4}
					unit="rpm{'\n'}x1000" 
					ranges={[
						{ min: 0, max: 5.99, colorClass: 'text-white' },
						{ min: 6, max: 6.99, colorClass: 'text-orange-500' },
						{ min: 7, max: 7.5, colorClass: 'text-red-500' }
					]}
					demo={true}
				/>
			</li>
			<li>
				<GMeter x={0.5} y={-1.2} maxG={3} demo={true}/>
			</li>
		</ul>
	</div>
	<div>
    <h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-3">Digital Cluster</h2>
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div class="col-span-1">
            <Speedometer 
                value={184} 
                unit="km/h" 
            />
        </div>

        <div class="col-span-1 lg:col-span-2">
            <Tachometer 
                value={6400} 
                max={7500}
                segments={75}
				stepSize={500}
                ranges={[
                    { min: 0, max: 5999, colorClass: 'bg-white' },
                    { min: 6000, max: 6999, colorClass: 'bg-orange-500' },
                    { min: 7000, max: 7500, colorClass: 'bg-red-500' }
                ]}
				demo={true}
            />
        </div>
		<Trackmap/>
    </div>
</div>
</section>