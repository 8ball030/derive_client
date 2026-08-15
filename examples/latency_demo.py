"""
Latency test script for the Derive HTTP API.

Features:
- click-based CLI
- configurable request count
- configurable concurrency (workers)
- configurable HTTP connection pool size
- detailed latency + throughput statistics
"""

import time
import statistics
from dataclasses import dataclass
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import click
from derive_client import HTTPClient
from derive_client.data_types.utils import D
from derive_client.data_types.generated_models import Direction, OrderType


# ---------- stats model ----------

@dataclass
class LatencyStats:
    count: int
    success_count: int
    error_count: int
    total_wall_time: float

    min: float
    max: float
    mean: float
    median: float
    stdev: float

    p50: float
    p90: float
    p95: float
    p99: float

    requests_per_second: float


# ---------- http ----------

def build_client(pool_size: int) -> HTTPClient:
    """
    Build a client with a configurable connection pool.
    Assumes derive_client delegates to requests/urllib3.
    """
    return HTTPClient.from_env()


def time_request(client: HTTPClient) -> Tuple[float, bool]:
    start = time.perf_counter()
    try:
        client.orders.create(
            instrument_name="BTC-PERP",
            amount=D("0.01"),
            limit_price=D("30000"),
            direction=Direction.buy,
            order_type=OrderType.limit,
        )
        ok = True
    except Exception as e:
        click.echo(f"Error occurred: {e}")
        ok = False
    end = time.perf_counter()
    return end - start, ok


def run_worker(client: HTTPClient, n: int) -> Tuple[List[float], int]:
    latencies: List[float] = []
    errors = 0

    for _ in range(n):
        latency, ok = time_request(client)
        if ok:
            latencies.append(latency)
        else:
            errors += 1

    return latencies, errors


# ---------- runner ----------

def perform_latency_test(
    num_requests: int,
    num_workers: int,
    pool_size: int,
) -> Tuple[List[float], int, float]:
    reqs_per_worker = num_requests // num_workers
    remainder = num_requests % num_workers

    all_latencies: List[float] = []
    total_errors = 0

    wall_start = time.perf_counter()

    client = build_client(pool_size)
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for i in range(num_workers):
            n = reqs_per_worker + (1 if i < remainder else 0)
            if n == 0:
                continue

            futures.append(executor.submit(run_worker, client, n))

        for fut in as_completed(futures):
            latencies, errors = fut.result()
            all_latencies.extend(latencies)
            total_errors += errors

    client.orders.cancel_all()
    wall_end = time.perf_counter()
    return all_latencies, total_errors, wall_end - wall_start


# ---------- analysis ----------

def percentile(samples: List[float], p: float) -> float:
    if not samples:
        raise ValueError("empty sample set")
    k = int(round((p / 100) * (len(samples) - 1)))
    return samples[k]


def analyze_latencies(
    latencies: List[float],
    errors: int,
    wall_time: float,
) -> LatencyStats:
    if not latencies:
        raise ValueError("no successful requests recorded")

    s = sorted(latencies)
    n = len(s)

    mean = statistics.mean(s)
    median = statistics.median(s)
    stdev = statistics.pstdev(s) if n > 1 else 0.0

    return LatencyStats(
        count=n,
        success_count=n,
        error_count=errors,
        total_wall_time=wall_time,
        min=s[0],
        max=s[-1],
        mean=mean,
        median=median,
        stdev=stdev,
        p50=percentile(s, 50),
        p90=percentile(s, 90),
        p95=percentile(s, 95),
        p99=percentile(s, 99),
        requests_per_second=n / wall_time if wall_time > 0 else 0.0,
    )


# ---------- presentation ----------

def print_stats(stats: LatencyStats) -> None:
    def ms(x: float) -> str:
        return f"{x * 1_000:.2f} ms"

    click.echo()
    click.secho("Derive API Latency Report", bold=True)
    click.echo()

    click.secho("Load", bold=True)
    click.echo(f"{'Successful':20} {stats.success_count}")
    click.echo(f"{'Errors':20} {stats.error_count}")
    click.echo(f"{'Wall time':20} {stats.total_wall_time:.3f} s")
    click.echo(f"{'Throughput':20} {stats.requests_per_second:.2f} req/s")
    click.echo()

    click.secho("Latency", bold=True)
    click.echo(f"{'Min':20} {ms(stats.min)}")
    click.echo(f"{'Mean':20} {ms(stats.mean)}")
    click.echo(f"{'Median':20} {ms(stats.median)}")
    click.echo(f"{'Std dev':20} {ms(stats.stdev)}")
    click.echo(f"{'Max':20} {ms(stats.max)}")
    click.echo()

    click.secho("Percentiles", bold=True)
    click.echo(f"{'P50':20} {ms(stats.p50)}")
    click.echo(f"{'P90':20} {ms(stats.p90)}")
    click.echo(f"{'P95':20} {ms(stats.p95)}")
    click.echo(f"{'P99':20} {ms(stats.p99)}")
    click.echo()


# ---------- cli ----------

@click.command()
@click.option("-n", "--num-requests", default=100, show_default=True, type=int)
@click.option("-w", "--num-workers", default=4, show_default=True, type=int)
@click.option("-p", "--pool-size", default=4, show_default=True, type=int)
def main(num_requests: int, num_workers: int, pool_size: int) -> None:
    latencies, errors, wall_time = perform_latency_test(
        num_requests=num_requests,
        num_workers=num_workers,
        pool_size=pool_size,
    )

    stats = analyze_latencies(latencies, errors, wall_time)
    print_stats(stats)


if __name__ == "__main__":
    main()
