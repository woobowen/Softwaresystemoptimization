import java.awt.Font;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.io.File;
import javax.imageio.ImageIO;

public class FontProbe {
    public static void main(String[] args) throws Exception {
        BufferedImage image = new BufferedImage(300, 80, BufferedImage.TYPE_INT_RGB);
        Graphics2D graphics = image.createGraphics();
        graphics.setFont(new Font("SansSerif", Font.PLAIN, 16));
        graphics.drawString("JDK 7 report font probe", 10, 40);
        graphics.dispose();
        ImageIO.write(image, "png", new File(args[0]));
        System.out.println("Font rendering completed");
    }
}
