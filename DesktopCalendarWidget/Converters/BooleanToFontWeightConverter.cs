using System;
using System.Globalization;
#if WINDOWS
using System.Windows;
using System.Windows.Data;
#endif

namespace DesktopCalendarWidget.Converters
{
    /// <summary>
    /// Converts boolean values to FontWeight values.
    /// Returns Bold if true, Normal if false.
    /// </summary>
#if WINDOWS
    public class BooleanToFontWeightConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is bool boolValue)
            {
                return boolValue ? FontWeights.Bold : FontWeights.Normal;
            }
            return FontWeights.Normal;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
#else
    public class BooleanToFontWeightConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is bool boolValue)
            {
                return boolValue ? "Bold" : "Normal";
            }
            return "Normal";
        }
    }
#endif
}