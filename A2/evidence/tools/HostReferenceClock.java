import java.io.BufferedReader;
import java.io.InputStreamReader;

/** Respond once to each Python sample request; EOF ends this process. */
public class HostReferenceClock {
    public static void main(String[] args) throws Exception {
        BufferedReader input = new BufferedReader(new InputStreamReader(System.in));
        System.out.println("READY");
        System.out.flush();
        String index;
        while ((index = input.readLine()) != null) {
            long wall = System.currentTimeMillis();
            long nano = System.nanoTime();
            System.out.println(index + " " + wall + " " + nano);
            System.out.flush();
        }
    }
}
