<script lang="ts">
	// Mock data for past racing sessions
	const recentSessions = [
		{ id: 'SESS-089', date: 'Oct 12, 2024', track: 'Spa-Francorchamps', type: 'Race', laps: 44, bestLap: '1:46.284', topSpeed: '312 km/h', status: 'Completed' },
		{ id: 'SESS-088', date: 'Oct 11, 2024', track: 'Spa-Francorchamps', type: 'Qualifying', laps: 14, bestLap: '1:44.902', topSpeed: '318 km/h', status: 'Completed' },
		{ id: 'SESS-087', date: 'Sep 28, 2024', track: 'Zolder', type: 'Race', laps: 30, bestLap: '1:29.410', topSpeed: '245 km/h', status: 'Completed' },
		{ id: 'SESS-086', date: 'Sep 28, 2024', track: 'Zolder', type: 'Practice', laps: 22, bestLap: '1:31.005', topSpeed: '241 km/h', status: 'Completed' }
	];
</script>

<section aria-labelledby="overview-heading" class="max-w-7xl mx-auto space-y-8">
	<header>
		<h1 id="overview-heading" class="text-3xl font-black text-white tracking-tight">Dashboard Overview</h1>
		<p class="text-zinc-400 text-sm mt-1">Select a past session to view detailed telemetry analytics.</p>
	</header>

	<div class="bg-zinc-900 border border-zinc-800 rounded-xl shadow-lg overflow-hidden">
		<div class="p-4 border-b border-zinc-800 bg-zinc-900/50">
			<h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest">Recent Sessions</h2>
		</div>
		
		<div class="overflow-x-auto">
			<table class="w-full text-left text-sm text-zinc-400 whitespace-nowrap">
				<thead class="text-xs uppercase bg-zinc-950/50 text-zinc-500 font-mono">
					<tr>
						<th scope="col" class="px-6 py-4 font-bold">Session ID</th>
						<th scope="col" class="px-6 py-4 font-bold">Track & Date</th>
						<th scope="col" class="px-6 py-4 font-bold">Type</th>
						<th scope="col" class="px-6 py-4 font-bold">Laps</th>
						<th scope="col" class="px-6 py-4 font-bold">Best Lap</th>
						<th scope="col" class="px-6 py-4 font-bold text-right">Action</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-zinc-800">
					{#each recentSessions as session}
						<tr class="hover:bg-zinc-800/50 transition-colors group">
							<td class="px-6 py-4 font-mono text-zinc-300">{session.id}</td>
							<td class="px-6 py-4">
								<div class="font-bold text-zinc-200">{session.track}</div>
								<div class="text-xs">{session.date}</div>
							</td>
							<td class="px-6 py-4">
								<span class="px-2 py-1 rounded text-[10px] font-black uppercase tracking-wider 
									{session.type === 'Race' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 
									 session.type === 'Qualifying' ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20' : 
									 'bg-blue-500/10 text-blue-400 border border-blue-500/20'}">
									{session.type}
								</span>
							</td>
							<td class="px-6 py-4 tabular-nums">{session.laps}</td>
							<td class="px-6 py-4 font-mono font-bold text-emerald-400">{session.bestLap}</td>
							<td class="px-6 py-4 text-right">
								<a 
									href="/analytics?session={session.id}" 
									class="inline-block px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white text-xs font-bold uppercase rounded transition-colors"
								>
									Analyze
								</a>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</div>
</section>