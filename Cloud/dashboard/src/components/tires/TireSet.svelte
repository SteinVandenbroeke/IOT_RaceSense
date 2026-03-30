<script lang="ts">
    import Tire from './Tire.svelte';

    interface Props {
        // Added 'auto' as the default behavior
        layout?: 'horizontal' | 'vertical' | 'auto';
        layerCount?: number;
    }

    let { layout = 'auto', layerCount = 3 }: Props = $props();

    // Default to a desktop width so it renders correctly on first load
    let innerWidth = $state(1024); 

    // Automatically switch to 'vertical' if the screen is smaller than 768px
    let activeLayout = $derived(
        layout === 'auto' 
            ? (innerWidth < 768 ? 'vertical' : 'horizontal') 
            : layout
    );
</script>

<svelte:window bind:innerWidth />

<div class="grid grid-cols-2 gap-x-4 sm:gap-x-6 gap-y-6 p-4 sm:p-5 max-w-2xl mx-auto">

    {#if activeLayout === 'horizontal'}
        <Tire statsPosition="left" {layerCount} />
        <Tire statsPosition="right" {layerCount} />

        <Tire statsPosition="left" {layerCount} />
        <Tire statsPosition="right" {layerCount} />

    {:else}
        <Tire statsPosition="top" {layerCount} />
        <Tire statsPosition="top" {layerCount} />

        <Tire statsPosition="bottom" {layerCount} />
        <Tire statsPosition="bottom" {layerCount} />
    {/if}

</div>