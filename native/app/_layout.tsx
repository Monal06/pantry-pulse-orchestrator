import React from "react";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { Text } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import InventoryScreen from "./screens/InventoryScreen";
import AddItemsScreen from "./screens/AddItemsScreen";
import ExitStrategyScreen from "./screens/ExitStrategyScreen";
import DashboardScreen from "./screens/DashboardScreen";
import MealsScreen from "./screens/MealsScreen";
import RecipesScreen from "./screens/RecipesScreen";

const Tab = createBottomTabNavigator();
const InventoryStack = createNativeStackNavigator();

function InventoryStackNavigator() {
  return (
    <InventoryStack.Navigator
      screenOptions={{
        headerShown: false,
      }}
    >
      <InventoryStack.Screen
        name="InventoryHome"
        component={InventoryScreen}
      />
      <InventoryStack.Screen
        name="AddItems"
        component={AddItemsScreen}
      />
    </InventoryStack.Navigator>
  );
}

function TabBarScreenOptions() {
  const insets = useSafeAreaInsets();

  return {
    headerShown: false,
    tabBarStyle: {
      backgroundColor: "#f8fafc",
      borderTopWidth: 2,
      borderTopColor: "#16a34a",
      paddingBottom: Math.max(insets.bottom, 8),
      paddingTop: 6,
      paddingHorizontal: 4,
      height: 65 + Math.max(insets.bottom, 8),
      elevation: 8,
      shadowColor: "#000",
      shadowOffset: { width: 0, height: -2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
    } as any,
    tabBarLabelStyle: {
      fontSize: 11,
      fontWeight: 700 as const,
      marginTop: 2,
    },
    tabBarActiveTintColor: "#16a34a",
    tabBarInactiveTintColor: "#1f2937",
    tabBarIconStyle: {
      marginBottom: 2,
    },
  };
}

export default function RootLayout() {
  const screenOptions = TabBarScreenOptions();

  return (
    <Tab.Navigator screenOptions={screenOptions}>
      <Tab.Screen
        name="InventoryTab"
        component={InventoryStackNavigator}
        options={{
          tabBarLabel: "Pantry",
          tabBarIcon: ({ color, size }) => (
            <Text style={{ fontSize: size, color }}>📦</Text>
          ),
        }}
      />
      <Tab.Screen
        name="ExitStrategyTab"
        component={ExitStrategyScreen}
        options={{
          tabBarLabel: "Life",
          tabBarIcon: ({ color, size }) => (
            <Text style={{ fontSize: size, color }}>🔄</Text>
          ),
        }}
      />
      <Tab.Screen
        name="MealsTab"
        component={MealsScreen}
        options={{
          tabBarLabel: "Meals",
          tabBarIcon: ({ color, size }) => (
            <Text style={{ fontSize: size, color }}>🍽️</Text>
          ),
        }}
      />
      <Tab.Screen
        name="RecipesTab"
        component={RecipesScreen}
        options={{
          tabBarLabel: "Recipes",
          tabBarIcon: ({ color, size }) => (
            <Text style={{ fontSize: size, color }}>❤️</Text>
          ),
        }}
      />
      <Tab.Screen
        name="DashboardTab"
        component={DashboardScreen}
        options={{
          tabBarLabel: "Impact",
          tabBarIcon: ({ color, size }) => (
            <Text style={{ fontSize: size, color }}>📊</Text>
          ),
        }}
      />
    </Tab.Navigator>
  );
}
