# DesktopCalendarWidget

This is a .NET class library that provides WPF value converters for the LXCloud Desktop Calendar Widget application.

## Converters Included

### StringToVisibilityConverter
Converts string values to WPF Visibility values:
- Returns `Visible` if the string is not null or empty
- Returns `Collapsed` if the string is null or empty

### BooleanToFontWeightConverter  
Converts boolean values to WPF FontWeight values:
- Returns `Bold` if true
- Returns `Normal` if false

### BooleanToBrushConverter
Converts boolean values to WPF Brush values:
- Returns `Green` brush if true
- Returns `Red` brush if false  
- Returns `Gray` brush if null

### NullToBooleanConverter
Converts null values to boolean values:
- Returns `true` if value is not null
- Returns `false` if value is null

## Usage

These converters are designed to be used in XAML bindings within a WPF application:

```xml
<Window.Resources>
    <converters:StringToVisibilityConverter x:Key="StringToVisibilityConverter" />
    <converters:BooleanToFontWeightConverter x:Key="BooleanToFontWeightConverter" />
    <converters:BooleanToBrushConverter x:Key="BooleanToBrushConverter" />
    <converters:NullToBooleanConverter x:Key="NullToBooleanConverter" />
</Window.Resources>
```

## Building

On Windows:
```
dotnet build
```

On non-Windows platforms, the converters build as a basic class library for compatibility.

## Namespace

All converters are in the `DesktopCalendarWidget.Converters` namespace.