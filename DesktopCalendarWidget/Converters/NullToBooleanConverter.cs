using System;
using System.Globalization;
#if WINDOWS
using System.Windows.Data;
#endif

namespace DesktopCalendarWidget.Converters
{
    /// <summary>
    /// Converts null values to boolean values.
    /// Returns true if value is not null, false if value is null.
    /// </summary>
#if WINDOWS
    public class NullToBooleanConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            return value != null;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
#else
    public class NullToBooleanConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            return value != null;
        }
    }
#endif
}