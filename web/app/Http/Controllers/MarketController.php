<?php

namespace App\Http\Controllers;

use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;
use Illuminate\View\View;
use PDO;
use Symfony\Component\Process\Process;

class MarketController extends Controller
{
    public function index(): View
    {
        return view('market');
    }

    public function data(): JsonResponse
    {
        $path = config('argentiq.database');
        $rows = [];

        if (is_file($path)) {
            try {
                $db = new PDO('sqlite:'.$path, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
                $rows = $db->query('SELECT item_id, city, quality, sell_price, sell_source_at, buy_price, buy_source_at, received_at FROM latest_observations ORDER BY item_id, city, quality')->fetchAll(PDO::FETCH_ASSOC);
            } catch (\PDOException $error) {
                Log::error('Market database read failed', ['error' => $error->getMessage()]);
                return response()->json(['message' => 'Saved market observations could not be read.'], 503);
            }
        }

        return response()->json([
            'server' => 'Asia',
            'checked_at' => now('UTC')->toIso8601String(),
            'timezone_note' => 'AODP source timestamps have no offset; ages provisionally assume UTC.',
            'rows' => $rows,
        ]);
    }

    public function refresh(Request $request): JsonResponse
    {
        $request->validate([
            'items' => ['required', 'string', 'regex:/^[A-Z0-9_@,]{1,160}$/'],
            'cities' => ['required', 'string', 'regex:/^[A-Za-z, ]{1,120}$/'],
            'quality' => ['required', 'integer', 'between:1,5'],
        ]);

        if (! Cache::add('argentiq-refresh-cooldown', true, now()->addSeconds(60))) {
            return response()->json(['message' => 'Please wait at least 60 seconds between refreshes.'], 429);
        }

        $process = new Process([
            config('argentiq.python'), '-m', 'argentiq',
            '--items', $request->string('items')->toString(),
            '--cities', $request->string('cities')->toString(),
            '--qualities', (string) $request->integer('quality'),
            '--db', config('argentiq.database'),
        ], dirname(base_path()));
        $process->setTimeout(60);

        try {
            $process->run();
        } catch (\Throwable $error) {
            Cache::forget('argentiq-refresh-cooldown');
            Log::error('Market refresh failed to start', ['error' => $error->getMessage()]);
            return response()->json(['message' => 'Collector could not start. Check the configured Python path.'], 503);
        }

        if (! $process->isSuccessful()) {
            Cache::forget('argentiq-refresh-cooldown');
            Log::warning('Market refresh failed', ['exit_code' => $process->getExitCode(), 'error' => $process->getErrorOutput()]);
            return response()->json(['message' => 'Refresh failed. Saved observations remain available. Check Laravel logs.'], 503);
        }

        return $this->data();
    }

    public function evidence(Request $request): JsonResponse
    {
        $request->validate([
            'item_id' => ['required', 'string', 'regex:/^[A-Z0-9_@]{1,80}$/'],
            'city' => ['required', 'string', 'regex:/^[A-Za-z]{1,80}$/'],
            'quality' => ['required', 'integer', 'between:1,5'],
        ]);

        $path = config('argentiq.database');
        if (! is_file($path)) {
            return response()->json(['message' => 'No saved observations yet.'], 404);
        }
        $db = new PDO('sqlite:'.$path, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
        $query = $db->prepare('SELECT sell_price, sell_source_at, buy_price, buy_source_at FROM latest_observations WHERE item_id = ? AND city = ? AND quality = ?');
        $query->execute([$request->string('item_id')->toString(), $request->string('city')->toString(), $request->integer('quality')]);
        $row = $query->fetch(PDO::FETCH_ASSOC);
        if (! $row) {
            return response()->json(['message' => 'That combination has no saved observation.'], 404);
        }

        $process = new Process([
            config('argentiq.java'), dirname(base_path()).DIRECTORY_SEPARATOR.'java'.DIRECTORY_SEPARATOR.'EvidenceGate.java',
            $row['sell_price'] ?? '-', $row['sell_source_at'] ?? '-',
            $row['buy_price'] ?? '-', $row['buy_source_at'] ?? '-',
            now('UTC')->toIso8601String(),
        ], dirname(base_path()));
        $process->setTimeout(15);
        try {
            $process->run();
        } catch (\Throwable $error) {
            return response()->json(['message' => 'Java evidence check is unavailable. Install a JDK and configure ARGENTIQ_JAVA.'], 503);
        }
        $result = json_decode($process->getOutput(), true);
        if (! $process->isSuccessful() || ! is_array($result) || ! isset($result['status'], $result['reason'])) {
            return response()->json(['message' => 'Java evidence check failed. Check the JDK configuration.'], 503);
        }
        return response()->json($result);
    }
}
