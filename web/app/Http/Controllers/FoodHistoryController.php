<?php

namespace App\Http\Controllers;

use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;
use Illuminate\View\View;
use PDO;
use PDOException;

class FoodHistoryController extends Controller
{
    private const CITIES = [
        7 => 'Thetford', 1002 => 'Lymhurst', 2004 => 'Bridgewatch',
        3005 => 'Caerleon', 3008 => 'Martlock', 4002 => 'Fort Sterling',
        5003 => 'Brecilien',
    ];

    public function index(): View
    {
        return view('food');
    }

    private function database(): ?PDO
    {
        $path = config('argentiq.food_database');
        if (! is_string($path) || ! is_file($path)) {
            return null;
        }

        return new PDO('sqlite:'.$path, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    }

    public function catalogue(): JsonResponse
    {
        try {
            $database = $this->database();
            if ($database === null) {
                return response()->json(['message' => 'Food history database is missing.'], 503);
            }
            $items = $database->query('SELECT item_id, display_name, food_type_code, tier, enchantment, history_rows_all_locations FROM food_coverage ORDER BY display_name, tier, enchantment')->fetchAll(PDO::FETCH_ASSOC);
            $locations = $database->query('SELECT DISTINCT location_id FROM food_history WHERE aggregation = 6 ORDER BY location_id')->fetchAll(PDO::FETCH_COLUMN);
            $qualities = $database->query('SELECT DISTINCT quality FROM food_history WHERE aggregation = 6 ORDER BY quality')->fetchAll(PDO::FETCH_COLUMN);

            return response()->json([
                'server' => 'Asia',
                'items' => $items,
                'qualities' => array_map('intval', $qualities),
                'locations' => array_map(fn ($id): array => [
                    'id' => (int) $id,
                    'name' => self::CITIES[(int) $id] ?? 'Location '.$id,
                ], $locations),
            ]);
        } catch (PDOException $error) {
            Log::error('Food catalogue read failed', ['error' => $error->getMessage()]);

            return response()->json(['message' => 'Food catalogue could not be read.'], 503);
        }
    }

    public function history(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'item_id' => ['required', 'string', 'regex:/^T[0-9]+_MEAL_[A-Z0-9_]+(?:@[0-9]+)?$/'],
            'location_id' => ['required', 'integer', 'min:1'],
            'quality' => ['required', 'integer', 'between:1,5'],
        ]);

        try {
            $database = $this->database();
            if ($database === null) {
                return response()->json(['message' => 'Food history database is missing.'], 503);
            }
            $catalogue = $database->prepare('SELECT display_name FROM food_items WHERE item_id = ?');
            $catalogue->execute([$validated['item_id']]);
            $item = $catalogue->fetch(PDO::FETCH_ASSOC);
            if ($item === false) {
                return response()->json(['message' => 'That food item is not in the catalogue.'], 404);
            }

            $query = $database->prepare('SELECT bucket_time_source, item_amount, silver_amount, source_sha256 FROM food_history WHERE item_id = ? AND location_id = ? AND quality = ? AND aggregation = 6 ORDER BY bucket_time_source');
            $query->execute([$validated['item_id'], $validated['location_id'], $validated['quality']]);
            $sourceRows = $query->fetchAll(PDO::FETCH_ASSOC);
            $sourceHashes = array_values(array_unique(array_column($sourceRows, 'source_sha256')));
            $points = array_map(static fn (array $row): array => [
                'bucket_time_source' => $row['bucket_time_source'],
                'item_amount' => (int) $row['item_amount'],
                'average_price' => (int) $row['item_amount'] > 0 ? round((int) $row['silver_amount'] / (int) $row['item_amount'], 2) : null,
                'review_flag' => null,
            ], $sourceRows);

            $missing = 0;
            for ($index = 1; $index < count($points); $index++) {
                $hours = (strtotime($points[$index]['bucket_time_source']) - strtotime($points[$index - 1]['bucket_time_source'])) / 3600;
                $missing += max(0, (int) round($hours / 6) - 1);
            }
            for ($index = 1; $index < count($points) - 1; $index++) {
                $previous = $points[$index - 1];
                $current = $points[$index];
                $following = $points[$index + 1];
                $leftHours = (strtotime($current['bucket_time_source']) - strtotime($previous['bucket_time_source'])) / 3600;
                $rightHours = (strtotime($following['bucket_time_source']) - strtotime($current['bucket_time_source'])) / 3600;
                if ($leftHours != 6 || $rightHours != 6 || $previous['average_price'] === null || $current['average_price'] === null || $following['average_price'] === null) {
                    continue;
                }
                if ($current['average_price'] < min($previous['average_price'], $following['average_price']) / 2) {
                    $points[$index]['review_flag'] = 'isolated_low';
                } elseif ($current['average_price'] > max($previous['average_price'], $following['average_price']) * 2) {
                    $points[$index]['review_flag'] = 'isolated_high';
                }
            }

            return response()->json([
                'server' => 'Asia',
                'item_id' => $validated['item_id'],
                'display_name' => $item['display_name'],
                'location_id' => (int) $validated['location_id'],
                'location_name' => self::CITIES[(int) $validated['location_id']] ?? 'Location '.$validated['location_id'],
                'quality' => (int) $validated['quality'],
                'aggregation_hours' => 6,
                'missing_buckets_between_first_and_last' => $missing,
                'review_flag_count' => count(array_filter($points, static fn (array $point): bool => $point['review_flag'] !== null)),
                'source_sha256s' => $sourceHashes,
                'points' => $points,
            ]);
        } catch (PDOException $error) {
            Log::error('Food history read failed', ['error' => $error->getMessage()]);

            return response()->json(['message' => 'Food history could not be read.'], 503);
        }
    }
}
