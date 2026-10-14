<?php

namespace Tests\Feature;

use PDO;
use Tests\TestCase;

class FoodHistoryPageTest extends TestCase
{
    private string $foodDatabasePath;

    protected function setUp(): void
    {
        parent::setUp();
        $this->foodDatabasePath = tempnam(sys_get_temp_dir(), 'food-history-test-');
        config()->set('argentiq.food_database', $this->foodDatabasePath);
        $database = new PDO('sqlite:'.$this->foodDatabasePath);
        $database->exec("CREATE TABLE food_items (item_id TEXT PRIMARY KEY, display_name TEXT, food_type_code TEXT, tier INTEGER, enchantment INTEGER);
            CREATE TABLE food_history (item_id TEXT, location_id INTEGER, quality INTEGER, aggregation INTEGER, bucket_time_source TEXT, item_amount INTEGER, silver_amount INTEGER, source_sha256 TEXT);
            CREATE TABLE import_runs (source_sha256 TEXT);
            INSERT INTO import_runs VALUES ('test-source');
            INSERT INTO food_items VALUES ('T8_MEAL_STEW', 'Beef Stew', 'STEW', 8, 0);
            INSERT INTO food_items VALUES ('T7_MEAL_STEW', 'Beef Stew', 'STEW', 7, 0);
            INSERT INTO food_history VALUES ('T8_MEAL_STEW', 2004, 1, 6, '2026-10-08 00:00:00.000000', 10, 50000, 'test-source');
            INSERT INTO food_history VALUES ('T8_MEAL_STEW', 2004, 1, 6, '2026-10-08 06:00:00.000000', 10, 10000, 'test-source');
            INSERT INTO food_history VALUES ('T8_MEAL_STEW', 2004, 1, 6, '2026-10-08 12:00:00.000000', 10, 50000, 'test-source');
            CREATE VIEW food_coverage AS SELECT item_id, display_name, food_type_code, tier, enchantment,
                (SELECT COUNT(*) FROM food_history h WHERE h.item_id = f.item_id) AS history_rows_all_locations FROM food_items f;");
    }

    protected function tearDown(): void
    {
        @unlink($this->foodDatabasePath);
        parent::tearDown();
    }

    public function test_food_page_and_catalogue_load(): void
    {
        $this->get('/')->assertOk()->assertSee('Asia food history');
        $this->getJson('/food-catalogue')
            ->assertOk()
            ->assertJsonCount(2, 'items')
            ->assertJsonPath('qualities.0', 1)
            ->assertJsonPath('locations.0.name', 'Bridgewatch');
    }

    public function test_history_calculates_price_and_flags_without_removing_observations(): void
    {
        $this->getJson('/food-history?item_id=T8_MEAL_STEW&location_id=2004&quality=1')
            ->assertOk()
            ->assertJsonPath('missing_buckets_between_first_and_last', 0)
            ->assertJsonPath('review_flag_count', 1)
            ->assertJsonPath('points.1.average_price', 1000)
            ->assertJsonPath('points.1.review_flag', 'isolated_low')
            ->assertJsonPath('source_sha256s.0', 'test-source')
            ->assertJsonCount(3, 'points');
    }

    public function test_catalogue_item_without_history_returns_empty_series(): void
    {
        $this->getJson('/food-history?item_id=T7_MEAL_STEW&location_id=2004&quality=1')
            ->assertOk()
            ->assertJsonPath('points', []);
    }
}
