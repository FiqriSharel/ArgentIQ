<?php

namespace Tests\Feature;

use Tests\TestCase;

class MarketPageTest extends TestCase
{
    public function test_local_market_page_loads(): void
    {
        $this->get('/')->assertOk()->assertSee('ArgentIQ');
    }

    public function test_market_api_labels_its_source_and_rows(): void
    {
        $this->getJson('/market-data')
            ->assertOk()
            ->assertJsonPath('server', 'Asia')
            ->assertJsonStructure(['checked_at', 'timezone_note', 'rows']);
    }

    public function test_refresh_rejects_invalid_item_ids_before_collection(): void
    {
        $this->postJson('/refresh', [
            'items' => 'T4_BAG;bad', 'cities' => 'Martlock', 'quality' => 1,
        ])->assertUnprocessable();
    }
}
