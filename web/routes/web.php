<?php

use App\Http\Controllers\FoodHistoryController;
use App\Http\Controllers\MarketController;
use Illuminate\Support\Facades\Route;

Route::get('/', [FoodHistoryController::class, 'index']);
Route::get('/food-catalogue', [FoodHistoryController::class, 'catalogue']);
Route::get('/food-history', [FoodHistoryController::class, 'history']);
Route::get('/market', [MarketController::class, 'index']);
Route::get('/market-data', [MarketController::class, 'data']);
Route::post('/refresh', [MarketController::class, 'refresh']);
Route::post('/evidence', [MarketController::class, 'evidence']);
