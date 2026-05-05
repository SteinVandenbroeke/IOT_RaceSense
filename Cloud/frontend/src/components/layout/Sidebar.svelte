<script lang="ts">
	let { isMenuOpen, closeMenu } = $props<{ isMenuOpen: boolean, closeMenu: () => void }>();

	const navLinks = [
		{ name: 'Dashboard Overview', href: '/', icon: '🏁' },
		{ name: 'Live Telemetry', href: '/live', icon: '📡' },
		{ name: 'Lap Analytics', href: '/analytics', icon: '📈' },
		{ name: 'Vehicle Settings', href: '/settings', icon: '🔧' }
	];
</script>

<aside
    class="fixed inset-y-0 left-0 z-50 w-64 border-r border-zinc-800 bg-zinc-900 flex flex-col transition-transform duration-300 lg:translate-x-0 lg:static lg:inset-auto
    {isMenuOpen ? 'translate-x-0' : '-translate-x-full'}"
>
    <header class="p-6 border-b border-zinc-800 flex justify-between items-center">
        <div>
            <h1 class="text-xl font-black tracking-tighter text-emerald-500">RACESENSE</h1>
            <p class="text-xs text-zinc-500 font-mono uppercase">Telemetry v1.0</p>
        </div>
        <button class="lg:hidden p-2 text-zinc-400" onclick={closeMenu} aria-label="Close menu">
            ✕
        </button>
    </header>

    <nav aria-label="Main Navigation" class="flex-1 p-4">
        <ul class="space-y-2">
            {#each navLinks as link}
                <li>
                    <a href={link.href} onclick={closeMenu} class="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-zinc-800 transition-colors group">
                        <span class="text-lg" aria-hidden="true">{link.icon}</span>
                        <span class="font-medium text-zinc-400 group-hover:text-white">{link.name}</span>
                    </a>
                </li>
            {/each}
        </ul>
    </nav>

    <footer class="p-4 border-t border-zinc-800 bg-zinc-900/80">
        <div class="flex items-center gap-2 px-2" role="status">
            <div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span class="text-xs font-mono text-zinc-400 uppercase">OBU Linked</span>
        </div>
    </footer>
</aside>