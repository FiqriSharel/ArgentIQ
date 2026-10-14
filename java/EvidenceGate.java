import java.time.Duration;
import java.time.Instant;

/** A conservative gate for future calculations. It never estimates profit. */
public class EvidenceGate {
    public static void main(String[] args) {
        if (args.length != 5) {
            System.out.println("{\"status\":\"blocked\",\"reason\":\"Invalid input\"}");
            return;
        }
        if (args[0].equals("-") || args[1].equals("-") || args[2].equals("-") || args[3].equals("-")) {
            System.out.println("{\"status\":\"blocked\",\"reason\":\"A buy or sell observation is unavailable\"}");
            return;
        }
        try {
            long sell = Long.parseLong(args[0]);
            long buy = Long.parseLong(args[2]);
            Instant sellAt = Instant.parse(args[1]);
            Instant buyAt = Instant.parse(args[3]);
            Instant now = Instant.parse(args[4]);
            if (sell <= 0 || buy <= 0) {
                System.out.println("{\"status\":\"blocked\",\"reason\":\"Invalid price\"}");
                return;
            }
            long sellAge = Duration.between(sellAt, now).toMinutes();
            long buyAge = Duration.between(buyAt, now).toMinutes();
            if (sellAge < -5 || buyAge < -5) {
                System.out.println("{\"status\":\"blocked\",\"reason\":\"Source clock anomaly\"}");
            } else if (sellAge > 360 || buyAge > 360) {
                System.out.println("{\"status\":\"blocked\",\"reason\":\"At least one quote is stale\"}");
            } else {
                System.out.println("{\"status\":\"reviewable\",\"reason\":\"Both observed quotes are recent; execution is not guaranteed\"}");
            }
        } catch (RuntimeException error) {
            System.out.println("{\"status\":\"blocked\",\"reason\":\"Malformed observation\"}");
        }
    }
}
