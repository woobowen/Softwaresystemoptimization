public class ClockProbe {
    public static void main(String[] args) throws Exception {
        long duration = Long.parseLong(args[0]) * 1000000000L;
        long start = System.nanoTime();
        while (true) {
            long nanos = System.nanoTime();
            System.out.println(System.currentTimeMillis() + " " + nanos);
            System.out.flush();
            if (nanos - start >= duration) break;
            Thread.sleep(1000);
        }
    }
}
