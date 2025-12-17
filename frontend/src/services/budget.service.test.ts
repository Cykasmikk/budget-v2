import { describe, it, expect, beforeEach, vi } from 'vitest';
import { BudgetService } from './budget.service';

describe('BudgetService', () => {
    let service: BudgetService;

    beforeEach(() => {
        service = BudgetService.getInstance();
        global.fetch = vi.fn();
    });

    it('should be a singleton', () => {
        const instance1 = BudgetService.getInstance();
        const instance2 = BudgetService.getInstance();
        expect(instance1).toBe(instance2);
    });

    it('should fetch rules', async () => {
        const mockRules = [
            { id: 1, pattern: '^AWS.*', category: 'Cloud' }
        ];
        
        (global.fetch as any).mockResolvedValueOnce({
            ok: true,
            json: () => Promise.resolve(mockRules)
        });

        const rules = await service.fetchRules();
        
        expect(global.fetch).toHaveBeenCalledWith('/api/v1/rules');
        expect(rules).toEqual(mockRules);
    });

    it('should add rule', async () => {
        (global.fetch as any).mockResolvedValueOnce({
            ok: true
        });

        await service.addRule('^AWS.*', 'Cloud');
        
        expect(global.fetch).toHaveBeenCalledWith('/api/v1/rules', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pattern: '^AWS.*', category: 'Cloud' })
        });
    });

    it('should delete rule', async () => {
        (global.fetch as any).mockResolvedValueOnce({
            ok: true
        });

        await service.deleteRule(1);
        
        expect(global.fetch).toHaveBeenCalledWith('/api/v1/rules/1', {
            method: 'DELETE'
        });
    });

    it('should throw error on failed fetch', async () => {
        (global.fetch as any).mockResolvedValueOnce({
            ok: false
        });

        await expect(service.fetchRules()).rejects.toThrow('Failed to fetch rules');
    });
});

