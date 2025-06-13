import { environment as dev } from './environment.dev';
import { environment as prod } from './environment.prod';

const isProd = import.meta.env.MODE === "production";

export const environment = isProd ? prod : dev;