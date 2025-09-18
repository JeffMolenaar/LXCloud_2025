using System;
using System.Globalization;
#if WINDOWS
using System.Windows;
using System.Windows.Data;
#endif

namespace DesktopCalendarWidget.Converters
{
    /// <summary>
    /// Converts string values to Visibility values.
    /// Returns Visible if string is not null or empty, otherwise Collapsed.
    /// </summary>
#if WINDOWS
    public class StringToVisibilityConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is string str)
            {
                return string.IsNullOrEmpty(str) ? Visibility.Collapsed : Visibility.Visible;
            }
            return value == null ? Visibility.Collapsed : Visibility.Visible;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
#else
    public class StringToVisibilityConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is string str)
            {
                return string.IsNullOrEmpty(str) ? "Collapsed" : "Visible";
            }
            return value == null ? "Collapsed" : "Visible";
        }
    }
#endif
}