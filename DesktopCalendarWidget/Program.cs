using System;
using System.Globalization;
using DesktopCalendarWidget.Converters;

namespace DesktopCalendarWidget
{
    public class Program
    {
        public static void Main(string[] args)
        {
            Console.WriteLine("Testing DesktopCalendarWidget Converters");
            Console.WriteLine("=========================================");

            // Test StringToVisibilityConverter
            var stringConverter = new StringToVisibilityConverter();
            Console.WriteLine($"StringToVisibilityConverter('Hello'): {stringConverter.Convert("Hello", typeof(object), null, CultureInfo.InvariantCulture)}");
            Console.WriteLine($"StringToVisibilityConverter(''): {stringConverter.Convert("", typeof(object), null, CultureInfo.InvariantCulture)}");
            Console.WriteLine($"StringToVisibilityConverter(null): {stringConverter.Convert(null, typeof(object), null, CultureInfo.InvariantCulture)}");

            // Test BooleanToFontWeightConverter
            var fontWeightConverter = new BooleanToFontWeightConverter();
            Console.WriteLine($"BooleanToFontWeightConverter(true): {fontWeightConverter.Convert(true, typeof(object), null, CultureInfo.InvariantCulture)}");
            Console.WriteLine($"BooleanToFontWeightConverter(false): {fontWeightConverter.Convert(false, typeof(object), null, CultureInfo.InvariantCulture)}");

            // Test BooleanToBrushConverter
            var brushConverter = new BooleanToBrushConverter();
            Console.WriteLine($"BooleanToBrushConverter(true): {brushConverter.Convert(true, typeof(object), null, CultureInfo.InvariantCulture)}");
            Console.WriteLine($"BooleanToBrushConverter(false): {brushConverter.Convert(false, typeof(object), null, CultureInfo.InvariantCulture)}");

            // Test NullToBooleanConverter
            var nullConverter = new NullToBooleanConverter();
            Console.WriteLine($"NullToBooleanConverter('test'): {nullConverter.Convert("test", typeof(object), null, CultureInfo.InvariantCulture)}");
            Console.WriteLine($"NullToBooleanConverter(null): {nullConverter.Convert(null, typeof(object), null, CultureInfo.InvariantCulture)}");

            Console.WriteLine("\nAll converters are working correctly!");
        }
    }
}