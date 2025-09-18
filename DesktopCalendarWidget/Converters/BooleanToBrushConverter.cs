using System;
using System.Globalization;
#if WINDOWS
using System.Windows.Data;
using System.Windows.Media;
#endif

namespace DesktopCalendarWidget.Converters
{
    /// <summary>
    /// Converts boolean values to Brush values.
    /// Returns a green brush if true, a red brush if false.
    /// </summary>
#if WINDOWS
    public class BooleanToBrushConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is bool boolValue)
            {
                return boolValue ? Brushes.Green : Brushes.Red;
            }
            return Brushes.Gray;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
#else
    public class BooleanToBrushConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is bool boolValue)
            {
                return boolValue ? "Green" : "Red";
            }
            return "Gray";
        }
    }
#endif
}