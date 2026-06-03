import { Router, type IRouter } from "express";
import healthRouter from "./health";
import activegraphRouter from "./activegraph";

const router: IRouter = Router();

router.use(healthRouter);
router.use(activegraphRouter);

export default router;
